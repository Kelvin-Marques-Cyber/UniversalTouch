"""Practice progression and a mouse sink with no operating-system side effects."""
import math


class TrainingMouse:
    def __init__(self):
        self.pointer = None
        self.held = False
        self.presses = 0

    def move_to(self,point): self.pointer = tuple(point)
    def press(self,button):
        if button == 'left' and not self.held:
            self.presses += 1
            self.held = True
    def release(self,button):
        if button == 'left': self.held = False
    def click(self,button):
        if button=='left':
            self.press(button)
            self.release(button)
    def scroll(self,steps): pass


class TutorialProgress:
    def __init__(self):
        self.stage = 0
        self.visited = 0
        self.stable = 0
        self.last_press = 0

    @property
    def done(self): return self.stage == 3

    @property
    def target(self):
        if self.stage == 1: return (.25,.5) if self.visited == 0 else (.75,.5)
        if self.stage == 2: return (.5,.5)
        return None

    def update(self,point,armed,presses,visible):
        new_press = presses > self.last_press
        self.last_press = presses
        if not visible or not armed or point is None:
            self.stable = 0
            return
        if self.stage == 0:
            self.stage = 1
            return
        target = self.target
        inside = target is not None and math.hypot(point[0]-target[0],point[1]-target[1]) <= .12
        if self.stage == 1:
            self.stable = self.stable+1 if inside else 0
            if self.stable >= 2:
                self.visited += 1
                self.stable = 0
                if self.visited == 2: self.stage = 2
        elif self.stage == 2 and inside and new_press:
            self.stage = 3
