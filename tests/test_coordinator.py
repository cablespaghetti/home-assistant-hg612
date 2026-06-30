from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hg612.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, DOMAIN
from custom_components.hg612.parser import HG612Stats

MOCK_STATS = HG612Stats(
    dsl_uptime_seconds=471173,
    downstream_kbps=36076,
    upstream_kbps=4795,
    max_downstream_kbps=36196,
    max_upstream_kbps=4809,
    system_uptime_seconds=654321.0,
)


@pytest.fixture
def config_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.1", CONF_USERNAME: "admin", CONF_PASSWORD: "admin"},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_fetch():
    with patch(
        "custom_components.hg612.coordinator.fetch_stats",
        new_callable=AsyncMock,
        return_value=MOCK_STATS,
    ) as m:
        yield m


async def test_sensors_created(hass, config_entry, mock_fetch):
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state == ConfigEntryState.LOADED
    assert hass.states.get("sensor.hg612_dsl_downstream_rate") is not None
    assert hass.states.get("sensor.hg612_dsl_upstream_rate") is not None
    assert hass.states.get("sensor.hg612_dsl_uptime") is not None


async def test_sensor_values(hass, config_entry, mock_fetch):
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.hg612_dsl_downstream_rate").state == "36076"
    assert hass.states.get("sensor.hg612_dsl_upstream_rate").state == "4795"
    uptime = hass.states.get("sensor.hg612_dsl_uptime")
    assert uptime.attributes["unit_of_measurement"] == "h"
    assert abs(float(uptime.state) - 471173 / 3600) < 0.01


async def test_setup_fails_on_connection_error(hass, config_entry):
    with patch(
        "custom_components.hg612.coordinator.fetch_stats",
        new_callable=AsyncMock,
        side_effect=ConnectionError("refused"),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state == ConfigEntryState.SETUP_RETRY


async def test_unload(hass, config_entry, mock_fetch):
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state == ConfigEntryState.NOT_LOADED
    assert hass.states.get("sensor.hg612_dsl_downstream_rate").state == "unavailable"
