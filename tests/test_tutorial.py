import unittest

from universal_touch.tutorial import TrainingMouse, TutorialProgress


class TutorialTests(unittest.TestCase):
    def test_cannot_progress_without_visible_armed_hand(self):
        progress = TutorialProgress()
        for _ in range(8): progress.update((.25,.5),False,3,False)
        self.assertEqual(progress.stage,0)

    def exercise_move(self,progress):
        progress.update((.5,.5),True,0,True)
        for point in [(.25,.5),(.25,.5),(.75,.5),(.75,.5)]:
            progress.update(point,True,0,True)

    def test_requires_visiting_both_targets_before_pinch(self):
        progress = TutorialProgress()
        self.exercise_move(progress)
        self.assertEqual(progress.stage,2)
        self.assertFalse(progress.done)
        progress.update((.5,.5),True,1,True)
        self.assertTrue(progress.done)

    def test_dragging_existing_pinch_into_target_is_not_a_new_click(self):
        progress = TutorialProgress()
        self.exercise_move(progress)
        progress.update((.1,.1),True,1,True)
        progress.update((.5,.5),True,1,True)
        self.assertFalse(progress.done)
        progress.update((.5,.5),True,2,True)
        self.assertTrue(progress.done)

    def test_lost_hand_cannot_complete_click_target(self):
        progress = TutorialProgress()
        self.exercise_move(progress)
        progress.update((.5,.5),False,1,False)
        self.assertFalse(progress.done)

    def test_training_mouse_records_gesture_without_os_input(self):
        mouse = TrainingMouse()
        mouse.move_to((.2,.3))
        mouse.press('left')
        mouse.press('left')
        self.assertEqual(mouse.presses,1)
        self.assertEqual(mouse.pointer,(.2,.3))
        mouse.release('left')
        mouse.press('left')
        self.assertEqual(mouse.presses,2)
