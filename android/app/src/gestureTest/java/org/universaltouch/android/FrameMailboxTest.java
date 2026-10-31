// SPDX-License-Identifier: Apache-2.0
package org.universaltouch.android;

public final class FrameMailboxTest {
    private static void check(boolean condition, String message) { if (!condition) throw new AssertionError(message); }
    private static GestureEngine.Frame sample(long time, boolean visible, boolean click, double x) {
        GestureEngine.Frame f = new GestureEngine.Frame(); f.time = time; f.visible = visible; f.click = click; f.x = x; return f;
    }
    public static void main(String[] args) {
        FrameMailbox box = new FrameMailbox();
        check(box.offer(sample(100, true, true, .4)), "first result must schedule delivery");
        check(!box.offer(sample(150, true, false, .8)), "coalesced movement must not schedule an unbounded queue");
        GestureEngine.Frame delivered = box.poll(180);
        check(delivered != null && delivered.click && delivered.x == .4, "movement must preserve a recent click and its position");
        box.offer(sample(200, true, true, .4));
        box.offer(sample(210, false, false, 0));
        check(!box.poll(220).click, "hand loss must cancel a pending action");
        box.offer(sample(300, true, true, .4));
        box.offer(sample(900, true, false, .8));
        delivered = box.poll(920);
        check(!delivered.click && delivered.x == .8, "a stalled UI must discard stale actions and use latest movement");
        System.out.println("FrameMailboxTest: all behavior checks passed");
    }
}
