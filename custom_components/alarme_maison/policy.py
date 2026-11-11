"""Routing rules independent of HA, with no automatic fallback or replay."""
import asyncio
import time

CLOUD = 'alarm_control_panel.alarme_meudon_centrale'
LOCAL = 'alarm_control_panel.diagral_local_centrale'
ALARM = 'alarm_control_panel.alarme_maison'
VALID_STATES = {'disarmed','armed_away','armed_home','armed_night','armed_custom_bypass','arming','disarming','pending','triggered'}

def selected_source(route, now=None):
    now = time.time() if now is None else now
    if not isinstance(route, dict):
        return None
    timestamp = route.get('checked_at')
    if not isinstance(timestamp, (int,float)) or not 0 <= now-timestamp < 30:
        return None
    return {'cloud':CLOUD,'local':LOCAL}.get(route.get('mode'))

def readable(source, state, attributes, now=None):
    if not source or state not in VALID_STATES | {'unknown'}:
        return False
    if source == LOCAL:
        stamp = attributes.get('derniere_lecture_epoch')
        now = time.time() if now is None else now
        return isinstance(stamp,(int,float)) and 0 <= now-stamp < 90
    return True

class SingleDispatch:
    def __init__(self):
        self.lock = asyncio.Lock()

    async def execute(self, service, resolve, forward):
        if service not in ('alarm_disarm','alarm_arm_away','alarm_arm_home'):
            raise ValueError('Commande non prise en charge')
        if self.lock.locked():
            raise ValueError('Une commande est déjà en cours')
        async with self.lock:
            source = await resolve()
            if source not in (LOCAL,CLOUD):
                raise ValueError('Pilote non vérifié ou indisponible')
            # One call only, even if the selected backend times out.
            await forward(service, source)
