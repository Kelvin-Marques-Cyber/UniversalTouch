import ctypes
from ctypes import wintypes
import threading
import time
import unittest

from universal_touch.backends import WindowsHotkeys


class Win32Boundary:
    """Win32 unavailable on Linux; model only the native message queue boundary."""
    def __init__(self):
        self.registrations = []
        self.unregistrations = []
        self.poll_threads = []
        self.messages = [1,2]

    def RegisterHotKey(self, window, key, modifiers, virtual_key):
        self.registrations.append((key,threading.get_ident()))
        return True

    def UnregisterHotKey(self, window, key):
        self.unregistrations.append((key,threading.get_ident()))
        return True

    def PeekMessageW(self, pointer, window, minimum, maximum, remove):
        self.poll_threads.append(threading.get_ident())
        if not self.messages: return 0
        pointer._obj.wParam = self.messages.pop(0)
        return 1


class HotkeyTests(unittest.TestCase):
    def test_registration_and_consumption_use_dedicated_thread_and_queue_actions(self):
        native = Win32Boundary()
        keys = WindowsHotkeys(native)
        try:
            deadline = time.monotonic()+1
            actions = []
            while len(actions) < 2 and time.monotonic() < deadline:
                actions.extend(keys.poll())
                time.sleep(.01)
            self.assertEqual(actions,['toggle','quit'])
            self.assertTrue(keys.available)
            worker = native.registrations[0][1]
            self.assertNotEqual(worker,threading.get_ident())
            self.assertEqual(set(native.poll_threads),{worker})
        finally:
            keys.close()
        self.assertEqual(native.unregistrations,[(1,worker),(2,worker)])
        self.assertFalse(keys.thread.is_alive())
