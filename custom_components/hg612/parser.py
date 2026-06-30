import re
from dataclasses import dataclass


@dataclass
class HG612Stats:
    dsl_uptime_seconds: int
    downstream_kbps: int
    upstream_kbps: int
    max_downstream_kbps: int
    max_upstream_kbps: int
    snr_downstream_db: float
    snr_upstream_db: float
    attn_downstream_db: float
    attn_upstream_db: float
    pwr_downstream_dbm: float
    pwr_upstream_dbm: float
    system_uptime_seconds: float


def parse_stats(text: str) -> HG612Stats:
    upstream_kbps = None
    downstream_kbps = None
    max_upstream_kbps = None
    max_downstream_kbps = None
    dsl_uptime_seconds = None
    snr_downstream_db = None
    snr_upstream_db = None
    attn_downstream_db = None
    attn_upstream_db = None
    pwr_downstream_dbm = None
    pwr_upstream_dbm = None

    for line in text.splitlines():
        if max_upstream_kbps is None and re.match(r"Max:\s+", line):
            m = re.search(r"Upstream rate = (\d+) Kbps, Downstream rate = (\d+) Kbps", line)
            if m:
                max_upstream_kbps = int(m.group(1))
                max_downstream_kbps = int(m.group(2))

        if upstream_kbps is None and re.match(r"Bearer:\s*0,", line):
            m = re.search(r"Upstream rate = (\d+) Kbps, Downstream rate = (\d+) Kbps", line)
            if m:
                upstream_kbps = int(m.group(1))
                downstream_kbps = int(m.group(2))

        if snr_downstream_db is None and re.match(r"SNR \(dB\):", line):
            m = re.search(r"([\d.]+)\s+([\d.]+)", line)
            if m:
                snr_downstream_db = float(m.group(1))
                snr_upstream_db = float(m.group(2))

        if attn_downstream_db is None and re.match(r"Attn\(dB\):", line):
            m = re.search(r"([\d.]+)\s+([\d.]+)", line)
            if m:
                attn_downstream_db = float(m.group(1))
                attn_upstream_db = float(m.group(2))

        if pwr_downstream_dbm is None and re.match(r"Pwr\(dBm\):", line):
            m = re.search(r"([\d.]+)\s+([\d.]+)", line)
            if m:
                pwr_downstream_dbm = float(m.group(1))
                pwr_upstream_dbm = float(m.group(2))

        if dsl_uptime_seconds is None and "Since Link time" in line:
            m = re.search(r"(\d+) days? (\d+) hours? (\d+) min (\d+) sec", line)
            if m:
                d, h, mi, s = map(int, m.groups())
                dsl_uptime_seconds = d * 86400 + h * 3600 + mi * 60 + s

    if any(
        v is None
        for v in [
            upstream_kbps,
            downstream_kbps,
            max_upstream_kbps,
            max_downstream_kbps,
            snr_downstream_db,
            snr_upstream_db,
            attn_downstream_db,
            attn_upstream_db,
            pwr_downstream_dbm,
            pwr_upstream_dbm,
            dsl_uptime_seconds,
        ]
    ):
        raise ValueError("Could not parse HG612 stats from output.")

    return HG612Stats(
        dsl_uptime_seconds=dsl_uptime_seconds,
        downstream_kbps=downstream_kbps,
        upstream_kbps=upstream_kbps,
        max_downstream_kbps=max_downstream_kbps,
        max_upstream_kbps=max_upstream_kbps,
        snr_downstream_db=snr_downstream_db,
        snr_upstream_db=snr_upstream_db,
        attn_downstream_db=attn_downstream_db,
        attn_upstream_db=attn_upstream_db,
        pwr_downstream_dbm=pwr_downstream_dbm,
        pwr_upstream_dbm=pwr_upstream_dbm,
        system_uptime_seconds=0.0,  # populated by fetch_stats from /proc/uptime
    )


def parse_system_uptime(text: str) -> float:
    """Parse the first field of /proc/uptime (seconds since boot, as a float)."""
    try:
        return float(text.split()[0])
    except (ValueError, IndexError) as err:
        raise ValueError(f"Could not parse /proc/uptime: {text!r}") from err
