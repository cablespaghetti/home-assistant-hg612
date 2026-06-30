import telnetlib3

from .const import DEFAULT_PORT
from .parser import HG612Stats, parse_stats

_TIMEOUT = 15


async def _read_until(reader: telnetlib3.TelnetReader, marker: str) -> str:
    buf = ""
    while marker not in buf:
        chunk = await reader.read(4096)
        if not chunk:
            raise ConnectionError(f"Connection closed before {marker!r} was received")
        buf += chunk
    return buf


async def fetch_stats(host: str, username: str, password: str) -> HG612Stats:
    reader, writer = await telnetlib3.open_connection(host, DEFAULT_PORT)
    try:
        await _read_until(reader, "Login:")
        writer.write(f"{username}\r\n")
        await _read_until(reader, "Password:")
        writer.write(f"{password}\r\n")
        await _read_until(reader, "ATP>")
        writer.write("sh\r\n")
        await _read_until(reader, "#")
        writer.write("xdslcmd info --stats\r\n")
        raw = await _read_until(reader, "#")
    finally:
        writer.close()

    return parse_stats(raw)
