"""OS mouse adapters. Never reads raw keyboards or changes permissions."""
import os
import sys
import queue
import threading


class WindowsHotkeys:
    """Own a message queue on a thread separate from Tcl/Tk's event loop."""
    def __init__(self, user):
        self.user = user
        self.actions = queue.SimpleQueue()
        self.stopped = threading.Event()
        self.ready = threading.Event()
        self.available = False
        self.thread = threading.Thread(target=self._listen,daemon=True,name='UniversalTouch-hotkeys')
        self.thread.start()
        self.ready.wait(1.)

    def _listen(self):
        import ctypes
        from ctypes import wintypes
        registered = []
        try:
            for key,mods in [(1,0x4003),(2,0x4007)]:
                if self.user.RegisterHotKey(None,key,mods,ord('G')):
                    registered.append(key)
            self.available = len(registered) == 2
            self.ready.set()
            message = wintypes.MSG()
            while not self.stopped.is_set():
                while self.user.PeekMessageW(ctypes.byref(message),None,0x312,0x312,1):
                    self.actions.put('quit' if message.wParam == 2 else 'toggle')
                self.stopped.wait(.02)
        finally:
            self.ready.set()
            for key in registered:
                self.user.UnregisterHotKey(None,key)

    def poll(self):
        actions = []
        while True:
            try: actions.append(self.actions.get_nowait())
            except queue.Empty: return actions

    def close(self):
        self.stopped.set()
        self.thread.join(timeout=1.)


class X11Mouse:
    name = 'Linux · X11'

    def __init__(self):
        from Xlib import X, XK, display
        from Xlib.ext import xtest
        self.X, self.xtest = X, xtest
        self.display = display.Display()
        if not self.display.has_extension('XTEST'):
            self.display.close()
            raise RuntimeError('O servidor X11 não oferece a extensão XTest.')
        self.root = self.display.screen().root
        self.held = set()
        self.keycode = self.display.keysym_to_keycode(XK.string_to_keysym('g'))
        self.hotkeys_available = True
        def on_error(error, request):
            self.hotkeys_available = False
        self.display.set_error_handler(on_error)
        for mods in (0, X.LockMask, X.Mod2Mask, X.LockMask | X.Mod2Mask):
            for shift in (0, X.ShiftMask):
                self.root.grab_key(self.keycode, X.ControlMask | X.Mod1Mask | shift | mods,
                                   False, X.GrabModeAsync, X.GrabModeAsync)
        self.display.sync()
        self.display.set_error_handler(None)

    def size(self):
        geometry = self.root.get_geometry()
        return geometry.width, geometry.height

    def move_to(self, point):
        w, h = self.size()
        self.xtest.fake_input(self.display, self.X.MotionNotify,
                             x=round(max(0,min(1,point[0]))*(w-1)),
                             y=round(max(0,min(1,point[1]))*(h-1)))
        self.display.flush()

    def press(self, button):
        self.xtest.fake_input(self.display, self.X.ButtonPress, detail={'left':1,'right':3}[button])
        self.held.add(button)
        self.display.flush()

    def release(self, button):
        if button in self.held:
            self.xtest.fake_input(self.display, self.X.ButtonRelease, detail={'left':1,'right':3}[button])
            self.held.discard(button)
            self.display.flush()

    def click(self, button):
        self.press(button)
        self.release(button)

    def scroll(self, steps):
        for _ in range(min(3,abs(int(steps)))):
            button = 4 if steps > 0 else 5
            self.xtest.fake_input(self.display, self.X.ButtonPress, detail=button)
            self.xtest.fake_input(self.display, self.X.ButtonRelease, detail=button)
        self.display.flush()

    def hotkeys(self):
        actions = []
        while self.display.pending_events():
            event = self.display.next_event()
            if event.type == self.X.KeyPress and event.detail == self.keycode:
                actions.append('quit' if event.state & self.X.ShiftMask else 'toggle')
        return actions

    def passthrough(self, window_id):
        from Xlib.ext import shape
        if not self.display.has_extension('SHAPE'):
            raise RuntimeError('SHAPE não disponível: indicador desativado para não bloquear cliques.')
        win = self.display.create_resource_object('window', window_id)
        win.shape_rectangles(shape.SO.Set, shape.SK.Input, self.X.Unsorted, 0, 0, [])
        # Tk creates an outer wrapper for a toplevel. Clearing only its client
        # child still leaves the wrapper intercepting the click at the cursor.
        parent = win.query_tree().parent
        if parent.id != self.root.id:
            parent.shape_rectangles(shape.SO.Set, shape.SK.Input, self.X.Unsorted, 0, 0, [])
        self.display.sync()

    def close(self):
        for button in list(self.held):
            self.release(button)
        self.root.ungrab_key(self.keycode, self.X.AnyModifier)
        self.display.sync()
        self.display.close()


class WindowsMouse:
    name = 'Windows · Win32'

    def __init__(self):
        import ctypes
        from ctypes import wintypes
        self.ctypes, self.wintypes = ctypes, wintypes
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.user.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
        self.user.SetCursorPos.restype = wintypes.BOOL
        self.user.GetParent.argtypes = [wintypes.HWND]
        self.user.GetParent.restype = wintypes.HWND
        self.user.mouse_event.argtypes = [wintypes.DWORD,wintypes.DWORD,wintypes.DWORD,wintypes.DWORD,ctypes.c_size_t]
        self.user.RegisterHotKey.argtypes = [wintypes.HWND,ctypes.c_int,wintypes.UINT,wintypes.UINT]
        self.user.UnregisterHotKey.argtypes = [wintypes.HWND,ctypes.c_int]
        self.user.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG),wintypes.HWND,wintypes.UINT,wintypes.UINT,wintypes.UINT]
        self.held = set()
        self.keys = WindowsHotkeys(self.user)
        self.hotkeys_available = self.keys.available

    def size(self):
        # Virtual desktop supports monitor origins left/above the primary one.
        return self.user.GetSystemMetrics(78), self.user.GetSystemMetrics(79)

    def move_to(self, point):
        w, h = self.size()
        x = self.user.GetSystemMetrics(76) + round(max(0,min(1,point[0]))*(w-1))
        y = self.user.GetSystemMetrics(77) + round(max(0,min(1,point[1]))*(h-1))
        if not self.user.SetCursorPos(x,y):
            raise RuntimeError('Windows impediu mover o cursor nesta área de trabalho.')

    def press(self, button):
        self.user.mouse_event({'left':2,'right':8}[button],0,0,0,0)
        self.held.add(button)

    def release(self, button):
        if button in self.held:
            self.user.mouse_event({'left':4,'right':16}[button],0,0,0,0)
            self.held.discard(button)

    def click(self, button):
        self.press(button)
        self.release(button)

    def scroll(self, steps):
        self.user.mouse_event(0x800,0,0,self.ctypes.c_uint32(int(steps)*120).value,0)

    def hotkeys(self):
        return self.keys.poll()

    def passthrough(self, window_id):
        hwnd = self.user.GetParent(window_id) or window_id
        # Pointer-sized APIs need pointer-sized signatures on 64-bit Windows.
        get_style = self.user.GetWindowLongPtrW if self.ctypes.sizeof(self.ctypes.c_void_p)==8 else self.user.GetWindowLongW
        set_style = self.user.SetWindowLongPtrW if self.ctypes.sizeof(self.ctypes.c_void_p)==8 else self.user.SetWindowLongW
        get_style.argtypes = [self.wintypes.HWND,self.ctypes.c_int]
        get_style.restype = self.ctypes.c_ssize_t
        set_style.argtypes = [self.wintypes.HWND,self.ctypes.c_int,self.ctypes.c_ssize_t]
        set_style.restype = self.ctypes.c_ssize_t
        set_style(hwnd,-20,get_style(hwnd,-20) | 0x80000 | 0x20 | 0x80 | 0x08000000)

    def close(self):
        for button in list(self.held): self.release(button)
        self.keys.close()


class WaylandMouse:
    name = 'Linux · Wayland/uinput'
    hotkeys_available = False

    def __init__(self):
        try:
            from evdev import UInput, AbsInfo, ecodes as e
        except ImportError as exc:
            raise RuntimeError('Wayland requer o extra evdev: instale UniversalTouch[wayland] ou use uma sessão X11.') from exc
        self.e = e
        self.held = set()
        try:
            self.device = UInput({
                e.EV_ABS:[(e.ABS_X,AbsInfo(0,0,65535,0,0,0)),(e.ABS_Y,AbsInfo(0,0,65535,0,0,0))],
                e.EV_KEY:[e.BTN_LEFT,e.BTN_RIGHT], e.EV_REL:[e.REL_WHEEL],
            }, name='UniversalTouch pointer')
        except OSError as exc:
            raise RuntimeError('Wayland precisa de acesso autorizado a /dev/uinput. Consulte docs/linux-wayland.md ou entre em uma sessão X11.') from exc

    def move_to(self, point):
        for axis, value in zip([self.e.ABS_X,self.e.ABS_Y],point):
            self.device.write(self.e.EV_ABS,axis,round(max(0,min(1,value))*65535))
        self.device.syn()

    def press(self, button):
        self.device.write(self.e.EV_KEY,{'left':self.e.BTN_LEFT,'right':self.e.BTN_RIGHT}[button],1)
        self.device.syn()
        self.held.add(button)

    def release(self, button):
        if button in self.held:
            self.device.write(self.e.EV_KEY,{'left':self.e.BTN_LEFT,'right':self.e.BTN_RIGHT}[button],0)
            self.device.syn()
            self.held.discard(button)

    def click(self, button):
        self.press(button)
        self.release(button)

    def scroll(self, steps):
        self.device.write(self.e.EV_REL,self.e.REL_WHEEL,max(-3,min(3,int(steps))))
        self.device.syn()

    def hotkeys(self): return []
    def close(self):
        for button in list(self.held): self.release(button)
        self.device.close()


def create_mouse():
    if sys.platform == 'win32':
        return WindowsMouse()
    if sys.platform == 'linux':
        if os.environ.get('XDG_SESSION_TYPE') == 'wayland' or os.environ.get('WAYLAND_DISPLAY'):
            return WaylandMouse()
        return X11Mouse()
    raise RuntimeError('Esta versão desktop suporta Windows e Linux.')


def set_dpi_awareness():
    if sys.platform == 'win32':
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (OSError,AttributeError):
            ctypes.windll.user32.SetProcessDPIAware()
