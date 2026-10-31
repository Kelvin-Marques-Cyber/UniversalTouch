// SPDX-License-Identifier: Apache-2.0
package org.universaltouch.android;

/** Bounded cross-thread handoff: latest movement plus one recent deliberate action. */
public final class FrameMailbox {
    private GestureEngine.Frame latest, action;
    private boolean scheduled;

    public synchronized boolean offer(GestureEngine.Frame frame) {
        latest = frame;
        if (!frame.visible) action = null;
        else if (frame.click || (frame.scroll != 0 && action == null)) action = frame;
        boolean needsDelivery = !scheduled;
        scheduled = true;
        return needsDelivery;
    }
    public synchronized GestureEngine.Frame poll(long now) {
        GestureEngine.Frame result = action != null && now - action.time >= 0 && now - action.time <= 350 ? action : latest;
        latest = action = null;
        scheduled = false;
        return result;
    }
}
