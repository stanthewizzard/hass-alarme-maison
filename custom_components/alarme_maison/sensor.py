"""Selected driver, independently of alarm availability."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import DOMAIN
from .policy import selected_source

async def async_setup_entry(hass,entry,async_add_entities):
    async_add_entities([DriverSensor(hass.data[DOMAIN][entry.entry_id])])

class DriverSensor(CoordinatorEntity,SensorEntity):
    _attr_name='Alarme Maison Pilote'
    _attr_unique_id='alarme_maison_pilote'
    _attr_icon='mdi:routes'
    def __init__(self,coordinator):
        super().__init__(coordinator)
        self._attr_device_info={'identifiers':{(DOMAIN,'maison')}}
    @property
    def available(self):return bool(super().available and selected_source(self.coordinator.data))
    @property
    def native_value(self):return (self.coordinator.data or {}).get('mode') if self.available else None
