// SPDX-License-Identifier: Apache-2.0
package org.universaltouch.android;

public final class TutorialProgressTest {
    private static void check(boolean ok, String why) { if (!ok) throw new AssertionError(why); }
    private static GestureEngine.Frame frame(long time, double x, double y, boolean visible, boolean armed, boolean click) {
        GestureEngine.Frame f = new GestureEngine.Frame(); f.time = time; f.x = x; f.y = y;
        f.visible = visible; f.armed = armed; f.click = click; return f;
    }
    public static void main(String[] args) {
        TutorialProgress p = new TutorialProgress();
        p.update(frame(0,.5,.5,false,false,false));
        p.update(frame(10,.5,.5,true,false,false));
        check(p.phase() == 0, "an absent or closed hand cannot pass the first practice step");
        p.update(frame(400,.5,.5,true,true,false));
        check(p.phase() == 1, "a real armed hand must begin movement practice");
        p.update(frame(500,.25,.35,true,true,false));
        check(p.targetsCompleted() == 0, "passing briefly through a target must not count");
        p.update(frame(850,.25,.35,true,true,false));
        check(p.targetsCompleted() == 1, "steady target contact must count");
        p.update(frame(900,.75,.35,true,true,false));
        p.update(frame(1000,0,0,false,false,false));
        p.update(frame(1250,.75,.35,true,true,false));
        check(p.targetsCompleted() == 1, "losing the hand must reset target dwell");
        p.update(frame(1600,.75,.35,true,true,false));
        p.update(frame(1700,.5,.7,true,true,false));
        p.update(frame(2050,.5,.7,true,true,false));
        check(p.phase() == 2, "all three movement targets must precede pinch practice");
        p.update(frame(2200,.1,.1,true,false,true));
        check(p.phase() == 2, "a pinch outside the final target must not complete training");
        p.update(frame(2400,.5,.5,true,false,true));
        check(p.phase() == 3, "a real pinch on the target must complete training");
        System.out.println("TutorialProgressTest: all practice checks passed");
    }
}
