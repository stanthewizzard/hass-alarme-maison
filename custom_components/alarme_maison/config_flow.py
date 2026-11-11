"""Configure the routing monitor; backend identifiers remain unchanged."""
import asyncio
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from . import DOMAIN
from .policy import selected_source

class ConfigFlow(config_entries.ConfigFlow,domain=DOMAIN):
    VERSION=1

    async def async_step_user(self,user_input=None):
        errors={}
        if user_input is not None:
            await self.async_set_unique_id('alarme_maison')
            self._abort_if_unique_id_configured()
            try:
                url=user_input['url'].rstrip('/')
                async with asyncio.timeout(8):
                    async with async_get_clientsession(self.hass).get(url+'/routing',headers={'Authorization':'Bearer '+user_input['token']}) as r:
                        r.raise_for_status()
                        if selected_source(await r.json()) is None:raise ValueError()
                return self.async_create_entry(title='Alarme Maison',data={'url':url,'token':user_input['token']})
            except Exception:
                errors['base']='cannot_connect'
        return self.async_show_form(step_id='user',data_schema=vol.Schema({
            vol.Required('url'):str,
            vol.Required('token'):str}),errors=errors)
