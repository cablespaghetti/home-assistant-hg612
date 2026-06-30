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


class TestParseStatsFromRealOutput:
    def test_downstream_rate(self):
        assert parse_stats(TESTDATA).downstream_kbps == 36076

    def test_upstream_rate(self):
        assert parse_stats(TESTDATA).upstream_kbps == 4795

    def test_dsl_uptime_seconds(self):
        assert parse_stats(TESTDATA).dsl_uptime_seconds == EXPECTED_UPTIME

    def test_bearer_0_used_not_bearer_1(self):
        # Bearer 1 has 0 Kbps rates — ensure we picked Bearer 0
        stats = parse_stats(TESTDATA)
        assert stats.upstream_kbps != 0
        assert stats.downstream_kbps != 0

    def test_max_downstream_rate(self):
        assert parse_stats(TESTDATA).max_downstream_kbps == 36196

    def test_max_upstream_rate(self):
        assert parse_stats(TESTDATA).max_upstream_kbps == 4809


class TestParseStatsEdgeCases:
    def test_crlf_line_endings(self):
        # Telnet delivers \r\n; parser must handle it
        stats = parse_stats(TESTDATA.replace("\n", "\r\n"))
        assert stats.downstream_kbps == 36076
        assert stats.upstream_kbps == 4795
        assert stats.dsl_uptime_seconds == EXPECTED_UPTIME

    def test_bearer_with_tab_separator(self):
        # Some firmware variants use a tab after the colon
        data = textwrap.dedent("""\
            Max:    Upstream rate = 1100 Kbps, Downstream rate = 2200 Kbps
            Bearer:\t0, Upstream rate = 1000 Kbps, Downstream rate = 2000 Kbps
            Since Link time = 0 days 1 hours 0 min 0 sec
        """)
        stats = parse_stats(data)
        assert stats.upstream_kbps == 1000
        assert stats.downstream_kbps == 2000

    def test_uptime_zero_days(self):
        data = textwrap.dedent("""\
            Max:    Upstream rate = 600 Kbps, Downstream rate = 1100 Kbps
            Bearer: 0, Upstream rate = 500 Kbps, Downstream rate = 1000 Kbps
            Since Link time = 0 days 0 hours 5 min 3 sec
        """)
        assert parse_stats(data).dsl_uptime_seconds == 5 * 60 + 3

    def test_uptime_many_days(self):
        data = textwrap.dedent("""\
            Max:    Upstream rate = 600 Kbps, Downstream rate = 1100 Kbps
            Bearer: 0, Upstream rate = 500 Kbps, Downstream rate = 1000 Kbps
            Since Link time = 99 days 23 hours 59 min 59 sec
        """)
        assert parse_stats(data).dsl_uptime_seconds == 99 * 86400 + 23 * 3600 + 59 * 60 + 59

    def test_missing_bearer_line_raises(self):
        with pytest.raises(ValueError):
            parse_stats("Since Link time = 1 days 0 hours 0 min 0 sec\n")

    def test_missing_uptime_line_raises(self):
        with pytest.raises(ValueError):
            parse_stats("Bearer: 0, Upstream rate = 500 Kbps, Downstream rate = 1000 Kbps\n")

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
