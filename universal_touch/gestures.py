"""Gesture state machine, independent of camera, GUI and operating system.

Copyright 2026 UniversalTouch contributors. SPDX-License-Identifier: Apache-2.0
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Result:
    status: str
    pointer: tuple | None = None
    pressed: bool = False
    progress: float = 0.


def distance(a, b):
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


class GestureController:
    """Translate 21 pixel landmarks into deliberate mouse events.

    The injected mouse owns only OS input. No event is generated while paused
    or until three consecutive open-hand frames have armed the controller.
    """
    def __init__(self, mouse, *, mirror=True, margin=0.15):
        self.mouse = mouse
        self.mirror = mirror
        self.margin = margin
        self.paused = True
        self.left_down = False
        self.armed = False
        self.ready = 0
        self.right_latched = False
        self.pointer = None
        self.last_time = None
        self.pinch_started = None
        self.scroll_y = None

    def _reset(self):
        if self.left_down:
            self.mouse.release('left')
        self.left_down = False
        self.armed = False
        self.ready = 0
        self.right_latched = False
        self.pointer = None
        self.last_time = None
        self.pinch_started = None
        self.scroll_y = None

    def set_paused(self, paused):
        self._reset()
        self.paused = bool(paused)

    def close(self):
        self.set_paused(True)

    def update(self, kp, shape, now):
        if self.paused:
            return Result('Pausado · câmera desligada')
        try:
            valid = (kp is not None and len(kp) == 21
                     and all(len(p) >= 2 and all(math.isfinite(float(v)) for v in p[:2]) for p in kp)
                     and shape[0] > 0 and shape[1] > 0 and math.isfinite(now))
        except (TypeError, ValueError, IndexError):
            valid = False
        if not valid:
            self._reset()
            return Result('Mostre a mão aberta')

        scale = max(distance(kp[5], kp[17]), distance(kp[0], kp[9]))
        if scale < 20:
            self._reset()
            return Result('Aproxime a mão da câmera')

        curled = [distance(kp[tip], kp[0]) < distance(kp[pip], kp[0])
                  for tip, pip in [(8,6),(12,10),(16,14),(20,18)]]
        left = distance(kp[4], kp[8]) / scale
        right = distance(kp[4], kp[12]) / scale
        if sum(curled) >= 3:
            self._reset()
            return Result('Punho fechado · cursor parado')

        if not self.armed:
            self.ready = self.ready + 1 if left > .60 and right > .60 and sum(curled) <= 1 else 0
            if self.ready < 3:
                return Result('Abra a mão para ativar')
            self.armed = True

        # A victory sign scrolls without moving or clicking the pointer.
        scrolling = not curled[0] and not curled[1] and curled[2] and curled[3]
        if scrolling and left > .60 and right > .60:
            if self.left_down:
                self.mouse.release('left')
                self.left_down = False
            y = float(kp[8][1]) / shape[0]
            if self.scroll_y is not None and abs(y - self.scroll_y) >= .045:
                self.mouse.scroll(-1 if y > self.scroll_y else 1)
                self.scroll_y = y
            elif self.scroll_y is None:
                self.scroll_y = y
            self.right_latched = False
            self.pinch_started = None
            return Result('Rolagem · mova dois dedos para cima/baixo', self.pointer)
        self.scroll_y = None

        if right > .60:
            self.right_latched = False
        right_pinched = right < .38 and right < left and not self.left_down
        if right_pinched:
            if not self.right_latched:
                self.mouse.click('right')
                self.right_latched = True
            return Result('Clique direito', self.pointer)

        want_left = left < (.60 if self.left_down else .38)
        if want_left and not self.left_down:
            self.mouse.press('left')
            self.left_down = True
            self.pinch_started = now
        elif not want_left and self.left_down:
            self.mouse.release('left')
            self.left_down = False
            self.pinch_started = None

        # Freeze briefly at pinch onset so clicking a small target does not
        # pull the cursor off it. Holding the pinch then enables dragging.
        if self.left_down and self.pinch_started is not None and now - self.pinch_started < .30:
            return Result('Clique · segure para arrastar', self.pointer, True)

        nx = float(kp[8][0]) / shape[1]
        ny = float(kp[8][1]) / shape[0]
        if self.mirror:
            nx = 1. - nx
        span = 1. - 2 * self.margin
        target = tuple(max(0., min(1., (v - self.margin) / span)) for v in (nx, ny))
        if self.pointer is None or self.last_time is None:
            self.pointer = target
        else:
            dt = max(.001, min(.25, now - self.last_time))
            delta = distance(target, self.pointer)
            speed = delta / dt
            # Adaptive smoothing: steady at rest, responsive over long moves.
            cutoff = min(16., 1.1 + 6. * speed)
            alpha = 1. - math.exp(-2. * math.pi * cutoff * dt)
            self.pointer = tuple(p + alpha * (v-p) for p, v in zip(self.pointer, target))
        self.last_time = now
        self.mouse.move_to(self.pointer)
        return Result('Arrastando' if self.left_down else 'Cursor ativo', self.pointer, self.left_down)
