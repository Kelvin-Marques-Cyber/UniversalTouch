// SPDX-License-Identifier: Apache-2.0
package org.universaltouch.android;

/** Time-based gesture safety and pointer smoothing, independent of camera frame rate. */
public final class GestureEngine {
    public static final class Frame {
        public boolean visible, armed, click;
        public long time;
        public double x, y, scroll;
    }
    private boolean tracked, armed, latched;
    private long openSince = -1, closeSince = -1, scrollSince = -1;
    private double x, y, clickX, clickY, scrollY;
    private double smoothing = .18;

    public void setSmoothing(double value) { smoothing = Math.max(.05, Math.min(.6, value)); }

    public void reset() {
        tracked = armed = latched = false;
        openSince = closeSince = scrollSince = -1;
    }

    public Frame update(long time, boolean hand, double targetX, double targetY, double pinch, boolean scrollPose) {
        Frame frame = new Frame();
        frame.time = time;
        if (!hand || !Double.isFinite(targetX) || !Double.isFinite(targetY) || !Double.isFinite(pinch)) {
            reset();
            return frame;
        }
        targetX = clamp(targetX);
        targetY = clamp(targetY);
        if (!tracked) {
            x = targetX;
            y = targetY;
            tracked = true;
        }
        double distance = Math.hypot(targetX - x, targetY - y);
        double alpha = Math.min(.85, smoothing + distance * .8);
        if (pinch < .5) alpha *= .3;
        x += (targetX - x) * alpha;
        y += (targetY - y) * alpha;
        frame.visible = true;
        frame.x = x;
        frame.y = y;

        if (scrollPose) {
            armed = false;
            openSince = closeSince = -1;
            if (scrollSince < 0) { scrollSince = time; scrollY = targetY; }
            if (time - scrollSince >= 250) {
                double delta = targetY - scrollY;
                if (Math.abs(delta) >= .04) {
                    frame.scroll = Math.max(-.3, Math.min(.3, delta));
                    scrollY = targetY;
                }
            }
        } else {
            scrollSince = -1;
            if (pinch >= .52) {
                closeSince = -1;
                if (openSince < 0) openSince = time;
                if (time - openSince >= 300) { armed = true; latched = false; }
            } else if (pinch <= .30) {
                openSince = -1;
                if (armed && !latched) {
                    if (closeSince < 0) { closeSince = time; clickX = x; clickY = y; }
                    if (time - closeSince >= 120) {
                        frame.click = true;
                        frame.x = clickX;
                        frame.y = clickY;
                        latched = true;
                        armed = false;
                    }
                }
            } else {
                closeSince = -1;
                openSince = -1;
            }
        }
        frame.armed = armed;
        return frame;
    }
    private static double clamp(double value) { return Math.max(0, Math.min(1, value)); }
}
