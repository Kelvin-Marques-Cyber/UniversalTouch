import sys
import unittest
from pathlib import Path

import numpy as np

from universal_touch.gestures import GestureController


class MouseRecorder:
    def __init__(self):
        self.events = []

    def move_to(self, p): self.events.append(('move', tuple(p)))
    def press(self, b): self.events.append(('press', b))
    def release(self, b): self.events.append(('release', b))
    def click(self, b): self.events.append(('click', b))
    def scroll(self, n): self.events.append(('scroll', n))


def open_hand():
    return np.array([
        (320,400),(270,350),(240,310),(215,280),(200,250),
        (280,300),(275,220),(275,170),(275,120),
        (320,280),(320,190),(320,140),(320,100),
        (360,300),(365,220),(365,170),(365,130),
        (395,330),(410,260),(420,220),(425,180),
    ], dtype=float)


class GestureTests(unittest.TestCase):
    def setUp(self):
        self.mouse = MouseRecorder()
        self.g = GestureController(self.mouse)

    def arm(self):
        self.g.set_paused(False)
        for t in [0., .1, .2]: self.g.update(open_hand(), (480,640,3), t)

    def pinch(self):
        hand = open_hand()
        hand[4] = hand[8]
        return hand

    def test_starts_paused_without_mouse_events(self):
        for t in range(5): self.g.update(self.pinch(), (480,640,3), t)
        self.assertEqual(self.mouse.events, [])

    def test_must_show_open_hand_before_clicking(self):
        self.g.set_paused(False)
        for t in range(5): self.g.update(self.pinch(), (480,640,3), t)
        self.assertEqual(self.mouse.events, [])
        self.arm()
        self.g.update(self.pinch(), (480,640,3), .3)
        self.assertIn(('press', 'left'), self.mouse.events)

    def test_losing_hand_releases_drag_and_requires_open_hand(self):
        self.arm()
        self.g.update(self.pinch(), (480,640,3), .3)
        self.g.update(None, (480,640,3), .4)
        self.assertEqual(self.mouse.events[-1], ('release', 'left'))
        previous = len(self.mouse.events)
        self.g.update(self.pinch(), (480,640,3), .5)
        self.assertEqual(len(self.mouse.events), previous)

    def test_pause_releases_button_and_suppresses_input(self):
        self.arm()
        self.g.update(self.pinch(), (480,640,3), .3)
        self.g.set_paused(True)
        self.assertEqual(self.mouse.events[-1], ('release', 'left'))
        previous = len(self.mouse.events)
        self.g.update(open_hand(), (480,640,3), .4)
        self.assertEqual(len(self.mouse.events), previous)

    def test_fist_releases_drag(self):
        self.arm()
        self.g.update(self.pinch(), (480,640,3), .3)
        hand = open_hand()
        for i in [8,12,16,20]: hand[i] = [320,380]
        self.g.update(hand, (480,640,3), .4)
        self.assertEqual(self.mouse.events[-1], ('release', 'left'))

    def test_right_pinch_clicks_once_until_released(self):
        self.arm()
        hand = open_hand()
        hand[4] = hand[12]
        for t in [.3,.4,.5]: self.g.update(hand, (480,640,3), t)
        self.assertEqual(self.mouse.events.count(('click','right')), 1)
        self.assertNotIn(('press','left'), self.mouse.events)

    def test_invalid_landmarks_release_drag_without_injection(self):
        self.arm()
        self.g.update(self.pinch(), (480,640,3), .3)
        hand = open_hand()
        hand[8,0] = np.nan
        self.g.update(hand, (480,640,3), .4)
        self.assertEqual(self.mouse.events[-1], ('release','left'))

    def test_scroll_with_two_fingers_does_not_press_buttons(self):
        self.arm()
        hand = open_hand()
        hand[16] = [365,340]
        hand[20] = [395,360]
        self.g.update(hand, (480,640,3), .3)
        hand[:,1] += 45
        self.g.update(hand, (480,640,3), .4)
        self.assertTrue(any(e[0] == 'scroll' for e in self.mouse.events))
        self.assertFalse(any(e[0] in ['press','click'] for e in self.mouse.events))

    def test_close_releases_drag(self):
        self.arm()
        self.g.update(self.pinch(), (480,640,3), .3)
        self.g.close()
        self.assertEqual(self.mouse.events[-1], ('release','left'))


if __name__ == '__main__': unittest.main()
