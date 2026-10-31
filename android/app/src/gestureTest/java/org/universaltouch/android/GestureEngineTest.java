// SPDX-License-Identifier: Apache-2.0
package org.universaltouch.android;

/** Pure Java tests: no camera or Android device is required. */
public final class GestureEngineTest {
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    private static GestureEngine.Frame frame(GestureEngine engine, long time, double pinch) {
        return engine.update(time, true, .5, .5, pinch, false);
    }
    public static void main(String[] args) {
        GestureEngine e = new GestureEngine();
        check(!frame(e, 0, .1).click, "closed hand at startup must not click");
        check(!frame(e, 500, .1).click, "holding startup pinch must not click");
        frame(e, 600, .8);
        check(frame(e, 950, .8).armed, "open hand must arm after a stable interval");
        check(!frame(e, 1000, .1).click, "pinch must debounce before clicking");
        check(frame(e, 1140, .1).click, "a deliberate pinch must click once");
        check(!frame(e, 1500, .1).click, "holding pinch must not repeat clicks");
        frame(e, 1600, .8);
        frame(e, 1950, .8);
        frame(e, 2000, .1);
        check(frame(e, 2140, .1).click, "release then new pinch must click again");
        e.update(2200, false, 0, 0, 0, false);
        check(!frame(e, 2300, .1).click, "lost hand must disarm before reacquisition");
        check(!frame(e, 2700, .1).armed, "reacquired closed hand remains disarmed");

        e = new GestureEngine();
        e.update(0, true, .3, .3, .9, false);
        GestureEngine.Frame moved = e.update(400, true, .9, .9, .9, false);
        check(moved.x > .3 && moved.x < .9, "smoothing must reduce pointer jumps");
        GestureEngine.Frame missing = e.update(500, false, 0, 0, 0, false);
        check(!missing.visible && !missing.armed, "lost hand must hide pointer and disarm");
        GestureEngine.Frame returned = e.update(600, true, .2, .2, .9, false);
        check(Math.abs(returned.x - .2) < .001, "reacquisition must discard stale position");

        e = new GestureEngine();
        e.update(0, true, .5, .5, .9, false);
        e.update(400, true, .5, .5, .9, false);
        e.update(500, true, .5, .5, .1, true);
        check(!e.update(700, true, .5, .3, .1, true).click, "scroll pose must suppress clicks");
        check(e.update(1100, true, .5, .1, .9, true).scroll < 0, "two finger movement must produce scroll after dwell");
        System.out.println("GestureEngineTest: all behavior checks passed");
    }
}
