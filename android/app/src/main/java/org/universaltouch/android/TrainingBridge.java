// SPDX-License-Identifier: Apache-2.0
package org.universaltouch.android;

/** Only the latest in-memory landmarks/result. No camera images, files, or queued events. */
public final class TrainingBridge {
    private TrainingBridge() { }
    public static volatile Sample latest;
    public static volatile boolean foreground;
    public static final class Sample {
        public final GestureEngine.Frame frame;
        public final double[] points;
        public Sample(GestureEngine.Frame frame, double[] points) { this.frame = frame; this.points = points; }
    }
    public static void publish(GestureEngine.Frame frame, double[] uprightPoints, boolean mirrored) {
        double[] points = frame.visible ? uprightPoints.clone() : null;
        if (points != null && mirrored) for (int i = 0; i < 42; i += 2) points[i] = 1 - points[i];
        latest = new Sample(frame, points);
    }
}
