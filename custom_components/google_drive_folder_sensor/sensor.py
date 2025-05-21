"""Platform for Google Drive Folder integration."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DATA_COORDINATOR,
    DOMAIN
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up Google Drive Folder sensor based on a config entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    unique_id = entry.data["auth_implementation"]

    name = "Files"
    unit = None
    icon = "mdi:file-multiple"
    device_class = None
    state_class = SensorStateClass.MEASUREMENT
    enabled_by_default = True
    sensor_type = "files"

    _LOGGER.debug("Registering entity: %s, %s, %s, %s, %s, %s, %s", sensor_type, name, unit, icon, device_class, state_class, enabled_by_default)
    async_add_entities([GoogleDriveFolderSensor(coordinator, unique_id, sensor_type, name, unit, icon, device_class, state_class, enabled_by_default)])

class GoogleDriveFolderSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Google Drive Folder sensor."""

    def __init__(
        self,
        coordinator,
        unique_id,
        sensor_type,
        name,
        unit,
        icon,
        device_class,
        state_class,
        enabled_default: bool = True,
    ):
        """Initialize a Google Drive Folder sensor."""
        super().__init__(coordinator)

        self._unique_id = unique_id
        self._type = sensor_type
        self._device_class = device_class
        self._state_class = state_class
        self._enabled_default = enabled_default

        self._attr_name = name
        self._attr_device_class = self._device_class
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"{self._unique_id}_{self._type}"
        self._attr_state_class = state_class

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self._type)
        return len(value)

    @property
    def extra_state_attributes(self):
        """Return attributes for sensor."""
        if not self.coordinator.data:
            return {}

        return {
            "last_synced": self.coordinator.data["lastSyncTimestampGMT"],
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._unique_id)},
            "name": "Google Drive Folder Sensor",
            "manufacturer": "Google Drive Folder Sensor",
        }

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._enabled_default

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and self.coordinator.data and self._type in self.coordinator.data