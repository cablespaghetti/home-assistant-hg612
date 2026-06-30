import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .parser import HG612Stats
from .telnet import fetch_stats

_LOGGER = logging.getLogger(__name__)


class HG612Coordinator(DataUpdateCoordinator[HG612Stats]):
    def __init__(self, hass: HomeAssistant, host: str, username: str, password: str) -> None:
        self.host = host
        self.username = username
        self.password = password
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> HG612Stats:
        try:
            return await fetch_stats(self.host, self.username, self.password)
        except Exception as err:
            raise UpdateFailed(f"HG612 telnet error: {err}") from err
