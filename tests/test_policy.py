"""Offline route and forwarding tests. No alarm or HA connection."""
import asyncio
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import AsyncMock

spec=importlib.util.spec_from_file_location('policy',Path(__file__).parents[1]/'custom_components/alarme_maison/policy.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class PolicyTests(unittest.TestCase):
    def test_local_and_cloud(self):
        self.assertEqual(p.selected_source({'mode':'local','checked_at':99},100),p.LOCAL)
        self.assertEqual(p.selected_source({'mode':'cloud','checked_at':99},100),p.CLOUD)
    def test_unknown_stale_and_future_route(self):
        for route in [None,{}, {'mode':'local','checked_at':70},{'mode':'cloud','checked_at':101},{'mode':'unknown','checked_at':99}]:
            self.assertIsNone(p.selected_source(route,100))
    def test_no_unavailable_backend_or_stale_local_state(self):
        self.assertFalse(p.readable(p.CLOUD,'unavailable',{},100))
        self.assertFalse(p.readable(p.LOCAL,'disarmed',{'derniere_lecture_epoch':1},100))
        self.assertTrue(p.readable(p.LOCAL,'disarmed',{'derniere_lecture_epoch':99},100))
    def test_unknown_local_code_keeps_connection_for_manual_stop(self):
        self.assertTrue(p.readable(p.LOCAL,'unknown',{'derniere_lecture_epoch':99},100))
        self.assertNotIn('unknown',p.VALID_STATES)

class DispatchTests(unittest.IsolatedAsyncioTestCase):
    async def test_one_driver_one_call(self):
        send=AsyncMock();resolve=AsyncMock(return_value=p.LOCAL)
        await p.SingleDispatch().execute('alarm_disarm',resolve,send)
        send.assert_awaited_once_with('alarm_disarm',p.LOCAL)
    async def test_failure_never_retries_or_falls_back(self):
        send=AsyncMock(side_effect=TimeoutError());resolve=AsyncMock(return_value=p.LOCAL)
        with self.assertRaises(TimeoutError):await p.SingleDispatch().execute('alarm_disarm',resolve,send)
        send.assert_awaited_once_with('alarm_disarm',p.LOCAL)
    async def test_mode_resolved_for_each_new_request(self):
        send=AsyncMock();resolve=AsyncMock(side_effect=[p.LOCAL,p.CLOUD]);d=p.SingleDispatch()
        await d.execute('alarm_arm_away',resolve,send)
        await d.execute('alarm_disarm',resolve,send)
        self.assertEqual([c.args[1] for c in send.await_args_list],[p.LOCAL,p.CLOUD])
    async def test_unverified_route_never_sends(self):
        send=AsyncMock()
        with self.assertRaises(ValueError):await p.SingleDispatch().execute('alarm_disarm',AsyncMock(return_value=None),send)
        send.assert_not_called()
    async def test_busy_does_not_queue(self):
        d=p.SingleDispatch();send=AsyncMock();resolve=AsyncMock(return_value=p.LOCAL)
        await d.lock.acquire()
        try:
            with self.assertRaises(ValueError):await d.execute('alarm_disarm',resolve,send)
            send.assert_not_called();resolve.assert_not_called()
        finally:d.lock.release()
if __name__=='__main__':unittest.main()
