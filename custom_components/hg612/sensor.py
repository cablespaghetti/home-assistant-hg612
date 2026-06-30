from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfDataRate, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HG612Coordinator
from .parser import HG612Stats


@dataclass(frozen=True, kw_only=True)
class HG612SensorDescription(SensorEntityDescription):
    value_fn: Callable[[HG612Stats], int | float]


SENSORS: tuple[HG612SensorDescription, ...] = (
    HG612SensorDescription(
        key="dsl_uptime",
        name="DSL Uptime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        suggested_display_precision=1,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.dsl_uptime_seconds,
    ),
    HG612SensorDescription(
        key="downstream_rate",
        name="DSL Downstream Rate",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.downstream_kbps,
    ),
    HG612SensorDescription(
        key="upstream_rate",
        name="DSL Upstream Rate",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.upstream_kbps,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HG612Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(HG612Sensor(coordinator, description) for description in SENSORS)


class HG612Sensor(CoordinatorEntity[HG612Coordinator], SensorEntity):
    entity_description: HG612SensorDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator: HG612Coordinator, description: HG612SensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.host}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": "HG612",
            "manufacturer": "Huawei",
            "model": "HG612",
        }

    @property
    def native_value(self) -> int | float | None:
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
