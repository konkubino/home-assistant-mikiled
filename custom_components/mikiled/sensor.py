"""Sensor platform for MiKiLED."""

from __future__ import annotations

from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MikiledCoordinator, MikiledDeviceData


def _temperature(data: MikiledDeviceData) -> StateType:
    if data.sensors and data.sensors.get("temperature") is not None:
        return float(data.sensors["temperature"])
    sensor = (data.status or {}).get("sensor") or {}
    if sensor.get("temperature") is not None:
        return float(sensor["temperature"])
    return None


def _humidity(data: MikiledDeviceData) -> StateType:
    if data.sensors and data.sensors.get("humidity") is not None:
        return float(data.sensors["humidity"])
    sensor = (data.status or {}).get("sensor") or {}
    if sensor.get("humidity") is not None:
        return float(sensor["humidity"])
    return None


def _truncate_str(value: StateType, max_len: int = 64) -> StateType:
    if isinstance(value, str) and len(value) > max_len:
        return value[:max_len]
    return value


def _firmware(data: MikiledDeviceData) -> StateType:
    if not data.version:
        return None
    return _truncate_str(data.version.get("version"))


def _api_version(data: MikiledDeviceData) -> StateType:
    if data.version and data.version.get("apiVersion") is not None:
        return _truncate_str(str(data.version["apiVersion"]), 16)
    if data.status and data.status.get("apiVersion") is not None:
        return _truncate_str(str(data.status["apiVersion"]), 16)
    return None


def _mode(data: MikiledDeviceData) -> StateType:
    if not data.status:
        return None
    raw = data.status.get("mode")
    if raw is None:
        return None
    return _truncate_str(str(raw), 32)


def _led_status(data: MikiledDeviceData) -> StateType:
    if not data.status:
        return None
    raw = data.status.get("ledStatus")
    if raw is None:
        return None
    return _truncate_str(str(raw), 32)


def _rssi(data: MikiledDeviceData) -> StateType:
    if not data.status:
        return None
    wifi = data.status.get("wifi") or {}
    if wifi.get("rssi") is None:
        return None
    return int(wifi["rssi"])


def _uptime(data: MikiledDeviceData) -> StateType:
    if not data.status:
        return None
    if data.status.get("uptime") is None:
        return None
    return int(data.status["uptime"])


SENSOR_TYPES: tuple[tuple[SensorEntityDescription, Callable[[MikiledDeviceData], StateType]], ...] = (
    (
        SensorEntityDescription(
            key="temperature",
            translation_key="temperature",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        _temperature,
    ),
    (
        SensorEntityDescription(
            key="humidity",
            translation_key="humidity",
            native_unit_of_measurement=PERCENTAGE,
            device_class=SensorDeviceClass.HUMIDITY,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        _humidity,
    ),
    (
        SensorEntityDescription(
            key="firmware",
            translation_key="firmware",
        ),
        _firmware,
    ),
    (
        SensorEntityDescription(
            key="api_version",
            translation_key="api_version",
        ),
        _api_version,
    ),
    (
        SensorEntityDescription(
            key="mode",
            translation_key="mode",
        ),
        _mode,
    ),
    (
        SensorEntityDescription(
            key="led_status",
            translation_key="led_status",
        ),
        _led_status,
    ),
    (
        SensorEntityDescription(
            key="wifi_rssi",
            translation_key="wifi_rssi",
            native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            device_class=SensorDeviceClass.SIGNAL_STRENGTH,
            state_class=SensorStateClass.MEASUREMENT,
            entity_registry_enabled_default=False,
        ),
        _rssi,
    ),
    (
        SensorEntityDescription(
            key="uptime",
            translation_key="uptime",
            native_unit_of_measurement="s",
            state_class=SensorStateClass.TOTAL_INCREASING,
            entity_registry_enabled_default=False,
        ),
        _uptime,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Register MiKiLED sensors."""
    coordinator: MikiledCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        MikiledSensor(coordinator, config_entry, description, value_fn)
        for description, value_fn in SENSOR_TYPES
    )


class MikiledSensor(CoordinatorEntity[MikiledCoordinator], SensorEntity):
    """Representation of a MiKiLED sensor."""

    def __init__(
        self,
        coordinator: MikiledCoordinator,
        config_entry: ConfigEntry,
        description: SensorEntityDescription,
        value_fn: Callable[[MikiledDeviceData], StateType],
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._value_fn = value_fn
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.title,
            manufacturer="MiKiLED",
            model="MiKiLED Controller",
            configuration_url=f"http://{coordinator.api.host}:{coordinator.api.port}/",
        )

    @property
    def native_value(self) -> StateType:
        """Return the sensor value."""
        return self._value_fn(self.coordinator.data)
