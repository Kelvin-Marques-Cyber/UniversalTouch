// SPDX-License-Identifier: Apache-2.0
package org.universaltouch.android;

import org.junit.Test;

/** Runs the same real behavior checks in the standard Android Gradle check lifecycle. */
public final class GestureUnitTest {
    @Test public void safetyAndSmoothing() { GestureEngineTest.main(new String[0]); }
    @Test public void boundedActionDelivery() { FrameMailboxTest.main(new String[0]); }
    @Test public void interactivePractice() { TutorialProgressTest.main(new String[0]); }
    @Test public void trainingNeverInjectsGestures() { FrameDispatcherTest.main(new String[0]); }
    @Test public void cameraOrientation() { CoordinateMapperTest.main(new String[0]); }
}
