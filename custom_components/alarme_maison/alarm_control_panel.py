"""Actual state and single forwarding; no fallback, no optimistic state."""
from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity,AlarmControlPanelState,AlarmControlPanelEntityFeature
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import DOMAIN
from .policy import CLOUD,LOCAL,VALID_STATES,selected_source,readable

async def async_setup_entry(hass,entry,async_add_entities):
    async_add_entities([MaisonAlarm(hass.data[DOMAIN][entry.entry_id])])

class MaisonAlarm(CoordinatorEntity,AlarmControlPanelEntity):
    _attr_name='Alarme Maison'
    _attr_unique_id='alarme_maison'
    _attr_code_arm_required=False

    def __init__(self,coordinator):
        super().__init__(coordinator)
        self._attr_device_info={'identifiers':{(DOMAIN,'maison')},'name':'Alarme Maison','manufacturer':'Intégration privée','model':'Routeur Diagral local/cloud','configuration_url':coordinator.entry.data['url']}

    @property
    def source(self):
        return selected_source(self.coordinator.data) if self.coordinator.last_update_success else None

    @property
    def backend(self):
        return self.hass.states.get(self.source) if self.source else None

    @property
    def available(self):
        state=self.backend
        return bool(super().available and state and readable(self.source,state.state,state.attributes))

    @property
    def alarm_state(self):
        state=self.backend
        return AlarmControlPanelState(state.state) if self.available and state.state in VALID_STATES else None

    @property
    def supported_features(self):
        state=self.backend
        mask=AlarmControlPanelEntityFeature.ARM_AWAY | AlarmControlPanelEntityFeature.ARM_HOME
        return int(state.attributes.get('supported_features',0)) & mask if state else 0

    @property
    def extra_state_attributes(self):
        return {'pilote':(self.coordinator.data or {}).get('mode') if self.source else 'unknown',
                'entite_source':self.source,'bascule_automatique':False,
                'verification_routage_epoch':(self.coordinator.data or {}).get('checked_at'),
                'routage_conserve':(self.coordinator.data or {}).get('routing_retained',False)}

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(async_track_state_change_event(self.hass,[CLOUD,LOCAL],self._backend_changed))

    @callback
    def _backend_changed(self,event):
        self.async_write_ha_state()

    async def _send(self,service,code):
        async def resolve():
            await self.coordinator.async_refresh()
            if (self.coordinator.data or {}).get('routing_retained'):
                return None
            if service != 'alarm_disarm' and (not self.backend or self.backend.state not in VALID_STATES):
                return None
            return self.source if self.available else None
        async def forward(service,source):
            data={'entity_id':source}
            if code is not None:data['code']=code
            await self.hass.services.async_call('alarm_control_panel',service,data,blocking=True,context=self._context)
        try:
            await self.coordinator.dispatcher.execute(service,resolve,forward)
        except HomeAssistantError:
            raise
        except Exception as exc:
            raise HomeAssistantError('Commande non confirmée ; aucune répétition ni bascule automatique') from exc
        self.async_write_ha_state()

    async def async_alarm_disarm(self,code=None):await self._send('alarm_disarm',code)
    async def async_alarm_arm_away(self,code=None):await self._send('alarm_arm_away',code)
    async def async_alarm_arm_home(self,code=None):await self._send('alarm_arm_home',code)
