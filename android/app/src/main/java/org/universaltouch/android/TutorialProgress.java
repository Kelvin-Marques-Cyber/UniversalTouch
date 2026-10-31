// SPDX-License-Identifier: Apache-2.0
package org.universaltouch.android;

/** Advances only from actual hand results, never from a Next button or a screen tap. */
public final class TutorialProgress {
    private static final double[][] TARGETS = {{.25,.35},{.75,.35},{.5,.7}};
    private int phase, completed;
    private long dwellSince = -1, lastFrame = -1;
    public int phase() { return phase; }
    public int targetsCompleted() { return completed; }
    public double targetX() { return phase == 1 ? TARGETS[completed][0] : .5; }
    public double targetY() { return phase == 1 ? TARGETS[completed][1] : .5; }
    public void update(GestureEngine.Frame frame) {
        if (frame.time <= lastFrame) return;
        lastFrame = frame.time;
        if (!frame.visible) { dwellSince = -1; return; }
        if (phase == 0) { if (frame.armed) phase = 1; return; }
        double distance = Math.hypot(frame.x - targetX(), frame.y - targetY());
        if (phase == 1) {
            if (distance > .13) { dwellSince = -1; return; }
            if (dwellSince < 0) dwellSince = frame.time;
            if (frame.time - dwellSince >= 300) { completed++; dwellSince = -1; if (completed == 3) phase = 2; }
        } else if (phase == 2 && distance <= .13 && frame.click) phase = 3;
    }
}
