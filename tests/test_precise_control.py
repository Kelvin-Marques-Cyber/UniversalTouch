import unittest
import numpy as np

from universal_touch.precise_control import PreciseController


class Mouse:
    def __init__(self):self.events=[]
    def move_to(self,p):self.events.append(('move',tuple(p)))
    def click(self,b):self.events.append(('click',b))
    def press(self,b):self.events.append(('press',b))
    def release(self,b):self.events.append(('release',b))
    def scroll(self,n):self.events.append(('scroll',n))
    def perform_action(self,a):self.events.append(('action',a));return True


def pose(fingers=1,dx=0.,dy=0.):
    p=np.array([(320,400),(270,350),(240,310),(215,280),(200,250),
        (280,300),(275,220),(275,170),(275,120),(320,280),(320,210),(320,170),(320,130),
        (360,300),(365,230),(365,190),(365,160),(395,330),(410,270),(420,230),(425,190)],float)
    for i,tip in enumerate([8,12,16,20]):
        if i>=fingers:p[tip]=p[0]+[i*4,-10]
    return p+np.array([dx,dy])


def pinched(dx=0.):
    p=pose(1,dx=dx)
    p[4]=p[8]
    return p


class PreciseTests(unittest.TestCase):
    def setUp(self):
        self.mouse=Mouse();self.c=PreciseController(self.mouse);self.c.set_paused(False)
        for i in range(3):self.c.update(pose(),(480,640,3),i*.1)

    def pinch(self,begin=.3):
        for i in range(3):self.c.update(pinched(),(480,640,3),begin+i*.1)

    def release(self,begin=.7):
        for i in range(3):self.c.update(pose(),(480,640,3),begin+i*.1)

    def test_only_index_pose_moves_without_automatic_click(self):
        for i in range(30):self.c.update(pose(1,dx=-20),(480,640,3),.3+i*.1)
        self.assertTrue(any(e[0]=='move' for e in self.mouse.events))
        self.assertFalse(any(e[0]=='click' for e in self.mouse.events))

    def test_click_is_frozen_during_entire_pinch_even_if_hand_moves(self):
        before=self.c.pointer
        self.pinch()
        for i in range(15):self.c.update(pinched(-80),(480,640,3),.6+i*.1)
        self.assertEqual(self.c.pointer,before)
        self.assertFalse(any(e[0]=='click' for e in self.mouse.events))
        self.release(2.3)
        self.assertEqual(self.mouse.events.count(('click','left')),1)
        self.assertEqual(self.c.pointer,before)

    def test_approaching_pinch_freezes_before_fingertips_meet(self):
        before=self.c.pointer
        p=pose(1,dx=50);p[4]=p[8]+[45,0]
        self.c.update(p,(480,640,3),.3)
        self.assertEqual(self.c.pointer,before)

    def test_hand_loss_cancels_click_without_emitting_it(self):
        self.pinch()
        self.c.update(None,(480,640,3),.7)
        self.release(.9)
        self.assertFalse(any(e[0]=='click' for e in self.mouse.events))

    def test_returning_with_closed_pinch_does_not_click(self):
        self.c.update(None,(480,640,3),.3)
        self.pinch(.5);self.release(1.)
        self.assertFalse(any(e[0]=='click' for e in self.mouse.events))

    def test_two_joined_fingers_scroll_with_frozen_pointer(self):
        before=self.c.pointer
        p=pose(2);p[12]=p[8]+[15,0]
        for i in range(4):self.c.update(p,(480,640,3),.3+i*.1)
        for i in range(5):self.c.update(p+[0,15*i],(480,640,3),.8+i*.1)
        self.assertTrue(any(e[0]=='scroll' for e in self.mouse.events))
        self.assertEqual(self.c.pointer,before)
        self.assertFalse(any(e[0]=='click' for e in self.mouse.events))

    def test_three_finger_swipe_runs_once_until_pose_released(self):
        p=pose(3);p[12]=p[8]+[18,0];p[16]=p[8]+[36,0]
        for i in range(4):self.c.update(p,(480,640,3),.3+i*.1)
        for i in range(5):self.c.update(p+[-80,0],(480,640,3),.8+i*.1)
        self.assertEqual(self.mouse.events.count(('action','workspace_next')),1)

    def test_three_finger_down_minimizes_once(self):
        p=pose(3);p[12]=p[8]+[18,0];p[16]=p[8]+[36,0]
        for i in range(4):self.c.update(p,(480,640,3),.3+i*.1)
        for i in range(5):self.c.update(p+[0,80],(480,640,3),.8+i*.1)
        self.assertEqual(self.mouse.events.count(('action','minimize')),1)

    def test_drag_requires_explicit_choice_and_releases_on_pause(self):
        self.c.set_action('drag');self.pinch()
        self.assertIn(('press','left'),self.mouse.events)
        self.c.set_paused(True)
        self.assertEqual(self.mouse.events[-1],('release','left'))

    def test_right_click_uses_explicit_choice_then_returns_to_left(self):
        self.c.set_action('right');self.pinch();self.release()
        self.pinch(1.2);self.release(1.7)
        self.assertEqual([e for e in self.mouse.events if e[0]=='click'],[('click','right'),('click','left')])

    def test_invalid_frame_releases_explicit_drag_and_cancels_click(self):
        self.c.set_action('drag');self.pinch()
        invalid=pose();invalid[8,0]=float('nan')
        self.c.update(invalid,(480,640,3),.7)
        self.assertEqual(self.mouse.events[-1],('release','left'))
        self.assertFalse(self.c.armed)

    def test_releasing_pinch_at_new_position_does_not_jump_pointer(self):
        before=self.c.pointer
        self.pinch()
        for i in range(12):self.c.update(pose(1,dx=60),(480,640,3),.7+i*.1)
        self.assertEqual(self.c.pointer,before)

    def test_two_finger_scroll_cannot_turn_into_thumb_middle_click(self):
        p=pose(2);p[12]=p[8]+[15,0];p[4]=p[12]
        self.c.update(p,(480,640,3),.3)
        self.c.update(p+[0,30],(480,640,3),.5)
        self.release(.8)
        self.assertFalse(any(e[0]=='click' for e in self.mouse.events))

    def test_pointing_resumes_after_scroll_without_reusing_old_samples(self):
        before=self.c.pointer
        p=pose(2);p[12]=p[8]+[15,0]
        self.c.update(p,(480,640,3),.3)
        self.c.update(p+[0,60],(480,640,3),.5)
        self.c.update(pose(1,dy=60),(480,640,3),.7)
        self.assertEqual(self.c.pointer,before)
