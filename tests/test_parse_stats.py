import importlib.util
import pathlib
import textwrap

import pytest

_parser_path = pathlib.Path(__file__).parent.parent / "custom_components" / "hg612" / "parser.py"
_spec = importlib.util.spec_from_file_location("hg612_parser", _parser_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

parse_stats = _mod.parse_stats
parse_system_uptime = _mod.parse_system_uptime

TESTDATA = (pathlib.Path(__file__).parent / "testdata.txt").read_text()

# 5 days * 86400 + 10 hours * 3600 + 52 min * 60 + 53 sec
EXPECTED_UPTIME = 5 * 86400 + 10 * 3600 + 52 * 60 + 53  # 471173


def test_parse_real_output():
    stats = parse_stats(TESTDATA)
    assert stats.downstream_kbps == 36076
    assert stats.upstream_kbps == 4795
    assert stats.max_downstream_kbps == 36196
    assert stats.max_upstream_kbps == 4809
    assert stats.snr_downstream_db == pytest.approx(3.6)
    assert stats.snr_upstream_db == pytest.approx(6.5)
    assert stats.attn_downstream_db == pytest.approx(25.6)
    assert stats.attn_upstream_db == pytest.approx(0.0)
    assert stats.pwr_downstream_dbm == pytest.approx(12.2)
    assert stats.pwr_upstream_dbm == pytest.approx(7.2)
    assert stats.dsl_uptime_seconds == EXPECTED_UPTIME
    # Bearer 1 has 0 Kbps — confirm we picked Bearer 0
    assert stats.upstream_kbps != 0
    assert stats.downstream_kbps != 0


MINIMAL_SNIPPET = textwrap.dedent("""\
    Max:    Upstream rate = 600 Kbps, Downstream rate = 1100 Kbps
    Bearer: 0, Upstream rate = 500 Kbps, Downstream rate = 1000 Kbps
    SNR (dB):        10.0             8.0
    Attn(dB):        20.0            5.0
    Pwr(dBm):        14.0            10.0
    Since Link time = {days} days {hours} hours {mins} min {secs} sec
""")


class TestParseStatsEdgeCases:
    def test_crlf_line_endings(self):
        # Telnet delivers \r\n; parser must handle it
        stats = parse_stats(TESTDATA.replace("\n", "\r\n"))
        assert stats.downstream_kbps == 36076
        assert stats.upstream_kbps == 4795
        assert stats.dsl_uptime_seconds == EXPECTED_UPTIME

    def test_bearer_with_tab_separator(self):
        # Some firmware variants use a tab after the colon
        data = MINIMAL_SNIPPET.replace("Bearer: 0,", "Bearer:\t0,").format(
            days=0, hours=1, mins=0, secs=0
        )
        stats = parse_stats(data)
        assert stats.upstream_kbps == 500
        assert stats.downstream_kbps == 1000

    def test_uptime_zero_days(self):
        data = MINIMAL_SNIPPET.format(days=0, hours=0, mins=5, secs=3)
        assert parse_stats(data).dsl_uptime_seconds == 5 * 60 + 3

    def test_uptime_many_days(self):
        data = MINIMAL_SNIPPET.format(days=99, hours=23, mins=59, secs=59)
        assert parse_stats(data).dsl_uptime_seconds == 99 * 86400 + 23 * 3600 + 59 * 60 + 59

    def test_missing_bearer_line_raises(self):
        data = MINIMAL_SNIPPET.format(days=1, hours=0, mins=0, secs=0).replace(
            "Bearer: 0, Upstream rate = 500 Kbps, Downstream rate = 1000 Kbps\n", ""
        )
        with pytest.raises(ValueError):
            parse_stats(data)

    def test_missing_uptime_line_raises(self):
        data = MINIMAL_SNIPPET.format(days=1, hours=0, mins=0, secs=0).replace(
            "Since Link time = 1 days 0 hours 0 min 0 sec\n", ""
        )
        with pytest.raises(ValueError):
            parse_stats(data)

    def test_empty_output_raises(self):
        with pytest.raises(ValueError):
            parse_stats("")


class TestParseSystemUptime:
    def test_typical_output(self):
        # /proc/uptime: seconds_since_boot idle_time
        assert parse_system_uptime("123456.78 234567.89\n") == pytest.approx(123456.78)

    def test_integer_seconds(self):
        assert parse_system_uptime("3600.00 1800.00\n") == pytest.approx(3600.0)

    def test_telnet_crlf(self):
        assert parse_system_uptime("98765.43 12345.67\r\n") == pytest.approx(98765.43)

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            parse_system_uptime("")

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError):
            parse_system_uptime("not a number\n")
