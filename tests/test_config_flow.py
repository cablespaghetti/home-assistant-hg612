from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.hg612.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, DOMAIN
from custom_components.hg612.parser import HG612Stats

MOCK_STATS = HG612Stats(
    dsl_uptime_seconds=471173,
    downstream_kbps=36076,
    upstream_kbps=4795,
    system_uptime_seconds=654321.0,
)
USER_INPUT = {CONF_HOST: "192.168.1.1", CONF_USERNAME: "admin", CONF_PASSWORD: "admin"}

_CF_FETCH = "custom_components.hg612.config_flow.fetch_stats"
_CO_FETCH = "custom_components.hg612.coordinator.fetch_stats"


@pytest.fixture
def mock_fetch():
    # Patch both usages: config_flow validates the connection, coordinator polls on entry setup
    with patch(_CF_FETCH, new_callable=AsyncMock, return_value=MOCK_STATS):
        with patch(_CO_FETCH, new_callable=AsyncMock, return_value=MOCK_STATS) as m:
            yield m


def _init_flow(hass):
    return hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def test_form_shown(hass):
    result = await _init_flow(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]


async def test_successful_setup(hass, mock_fetch):
    await _init_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        next(iter(hass.config_entries.flow._progress)),
        USER_INPUT,
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "HG612 (192.168.1.1)"
    assert result["data"] == USER_INPUT


async def test_cannot_connect_shows_error(hass):
    with patch(_CF_FETCH, new_callable=AsyncMock, side_effect=ConnectionError("refused")):
        await _init_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            next(iter(hass.config_entries.flow._progress)),
            USER_INPUT,
        )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_parse_error_shows_error(hass):
    with patch(_CF_FETCH, new_callable=AsyncMock, side_effect=ValueError("bad output")):
        await _init_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            next(iter(hass.config_entries.flow._progress)),
            USER_INPUT,
        )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_parse"}


async def test_duplicate_entry_aborted(hass, mock_fetch):
    for _ in range(2):
        flow_id = (await _init_flow(hass))["flow_id"]
        result = await hass.config_entries.flow.async_configure(flow_id, USER_INPUT)

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
