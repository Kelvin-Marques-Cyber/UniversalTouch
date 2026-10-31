// SPDX-License-Identifier: Apache-2.0
package org.universaltouch.android;

import java.util.function.Consumer;

/** The destination is immutable for a camera session; training cannot fall through to control. */
public final class FrameDispatcher {
    private final Consumer<GestureEngine.Frame> destination;
    public FrameDispatcher(boolean training, Consumer<GestureEngine.Frame> practice, Consumer<GestureEngine.Frame> control) {
        destination = training ? practice : control;
    }
    public void send(GestureEngine.Frame frame) { destination.accept(frame); }
}
