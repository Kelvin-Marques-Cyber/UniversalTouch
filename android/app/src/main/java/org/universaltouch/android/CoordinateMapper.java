// SPDX-License-Identifier: Apache-2.0
package org.universaltouch.android;

/** MediaPipe projects results back to the raw input; rotate them into the upright view. */
public final class CoordinateMapper {
    private CoordinateMapper() { }
    public static double rotateX(double x, double y, int rotation) {
        switch (rotation) {
            case 0: return x;
            case 90: return 1 - y;
            case 180: return 1 - x;
            case 270: return y;
            default: throw new IllegalArgumentException("Rotation must be a right angle");
        }
    }
    public static double rotateY(double x, double y, int rotation) {
        switch (rotation) {
            case 0: return y;
            case 90: return x;
            case 180: return 1 - y;
            case 270: return 1 - x;
            default: throw new IllegalArgumentException("Rotation must be a right angle");
        }
    }
}
