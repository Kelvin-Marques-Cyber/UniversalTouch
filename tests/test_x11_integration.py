"""Opt-in real input test, constrained to a dedicated temporary window."""
import os
import sys
import time
import unittest


@unittest.skipUnless(os.environ.get('UNIVERSALTOUCH_INPUT_TEST') == '1' and sys.platform == 'linux',
                     'explicit real X11 input test only')
class X11IntegrationTests(unittest.TestCase):
    def test_hint_at_top_left_does_not_wrap_to_opposite_edge(self):
        import tkinter as tk
        from universal_touch.backends import X11Mouse
        from universal_touch.app import CursorHint
        root = tk.Tk()
        root.withdraw()
        mouse = X11Mouse()
        hint = CursorHint(root,mouse)
        try:
            hint.show((0.,0.))
            root.update()
            self.assertEqual((hint.window.winfo_rootx(),hint.window.winfo_rooty()),(-14,-14))
        finally:
            hint.close()
            mouse.close()
            root.destroy()

    def test_mouse_and_click_through_hint(self):
        import tkinter as tk
        from universal_touch.backends import X11Mouse
        from universal_touch.app import CursorHint
        mouse = X11Mouse()
        position = mouse.root.query_pointer()
        old_focus = mouse.display.get_input_focus().focus
        root = tk.Tk()
        root.title('UniversalTouch input verification')
        root.geometry('220x180+50+50')
        root.attributes('-topmost',True)
        events = []
        for event,label in [('<ButtonPress-1>','left_down'),('<ButtonRelease-1>','left_up'),
                            ('<ButtonPress-3>','right'),('<ButtonPress-4>','scroll')]:
            root.bind(event,lambda e,label=label: events.append(label))
        root.update()
        root.focus_force()
        root.update()
        # Wait for the window manager to map the test surface before injecting.
        deadline = time.monotonic()+1.
        while time.monotonic() < deadline:
            root.update()
            time.sleep(.01)
        width,height = mouse.size()
        point = ((root.winfo_rootx()+100)/(width-1),(root.winfo_rooty()+80)/(height-1))
        hint = CursorHint(root,mouse)
        try:
            mouse.move_to(point)
            hint.show(point)
            root.update()
            mouse.click('left')
            mouse.click('right')
            mouse.scroll(1)
            deadline = time.monotonic()+2.
            while len(events) < 4 and time.monotonic() < deadline:
                root.update()
                time.sleep(.01)
            self.assertEqual(events,['left_down','left_up','right','scroll'])
            self.assertEqual(mouse.held,set())
        finally:
            hint.close()
            mouse.move_to((position.root_x/(width-1),position.root_y/(height-1)))
            try:
                from Xlib import X
                old_focus.set_input_focus(X.RevertToPointerRoot,X.CurrentTime)
            except (AttributeError,TypeError):
                pass
            root.destroy()
            mouse.close()
