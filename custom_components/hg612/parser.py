import re
from dataclasses import dataclass


@dataclass
class HG612Stats:
    dsl_uptime_seconds: int
    downstream_kbps: int
    upstream_kbps: int
    system_uptime_seconds: float


def parse_stats(text: str) -> HG612Stats:
    upstream_kbps = None
    downstream_kbps = None
    dsl_uptime_seconds = None

    for line in text.splitlines():
        if upstream_kbps is None and re.match(r"Bearer:\s*0,", line):
            m = re.search(r"Upstream rate = (\d+) Kbps, Downstream rate = (\d+) Kbps", line)
            if m:
                upstream_kbps = int(m.group(1))
                downstream_kbps = int(m.group(2))

        if dsl_uptime_seconds is None and "Since Link time" in line:
            m = re.search(r"(\d+) days? (\d+) hours? (\d+) min (\d+) sec", line)
            if m:
                d, h, mi, s = map(int, m.groups())
                dsl_uptime_seconds = d * 86400 + h * 3600 + mi * 60 + s

    if upstream_kbps is None or downstream_kbps is None or dsl_uptime_seconds is None:
        raise ValueError("Could not parse HG612 stats from output.")

    return HG612Stats(
        dsl_uptime_seconds=dsl_uptime_seconds,
        downstream_kbps=downstream_kbps,
        upstream_kbps=upstream_kbps,
        system_uptime_seconds=0.0,  # populated by fetch_stats from /proc/uptime
    )


def parse_system_uptime(text: str) -> float:
    """Parse the first field of /proc/uptime (seconds since boot, as a float)."""
    try:
        return float(text.split()[0])
    except (ValueError, IndexError) as err:
        raise ValueError(f"Could not parse /proc/uptime: {text!r}") from err
