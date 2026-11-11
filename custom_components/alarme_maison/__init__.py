"""Single alarm facade, selected by verified OPNsense routing via Docker."""
import asyncio
from datetime import timedelta
import logging
from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .policy import selected_source, SingleDispatch

DOMAIN='alarme_maison'
PLATFORMS=[Platform.ALARM_CONTROL_PANEL,Platform.SENSOR]

class RouterCoordinator(DataUpdateCoordinator):
    def __init__(self,hass,entry):
        super().__init__(hass,logging.getLogger(__name__),name='Alarme Maison',update_interval=timedelta(seconds=10))
        self.entry=entry
        self.dispatcher=SingleDispatch()

    async def _async_update_data(self):
        try:
            async with asyncio.timeout(8):
                async with async_get_clientsession(self.hass).get(
                    self.entry.data['url'].rstrip('/')+'/routing',
                    headers={'Authorization':'Bearer '+self.entry.data['token']}) as response:
                    response.raise_for_status()
                    result=await response.json()
            if selected_source(result) is None:
                raise ValueError('Routing not freshly confirmed')
            return result
        except Exception as exc:
            raise UpdateFailed('Mode local/cloud non confirmé par OPNsense') from exc

async def async_setup_entry(hass,entry):
    coordinator=RouterCoordinator(hass,entry)
    # Create unavailable entities even when Docker is down; never restore a guessed route.
    await coordinator.async_refresh()
    hass.data.setdefault(DOMAIN,{})[entry.entry_id]=coordinator
    await hass.config_entries.async_forward_entry_setups(entry,PLATFORMS)
    return True

async def async_unload_entry(hass,entry):
    if await hass.config_entries.async_unload_platforms(entry,PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id,None)
        return True
    return False
