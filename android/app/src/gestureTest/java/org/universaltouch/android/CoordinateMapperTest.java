// SPDX-License-Identifier: Apache-2.0
package org.universaltouch.android;

public final class CoordinateMapperTest {
    private static void point(int rotation, double expectedX, double expectedY) {
        double x = CoordinateMapper.rotateX(.2, .3, rotation);
        double y = CoordinateMapper.rotateY(.2, .3, rotation);
        if (Math.abs(x - expectedX) > .000001 || Math.abs(y - expectedY) > .000001)
            throw new AssertionError("Clockwise " + rotation + "° must map (.2,.3) to (" + expectedX + "," + expectedY + "), got (" + x + "," + y + ")");
    }
    public static void main(String[] args) {
        point(0, .2, .3);
        point(90, .7, .2);
        point(180, .8, .7);
        point(270, .3, .8);
        // A vertical movement in the upright portrait image must remain vertical after input rotation.
        double firstX = CoordinateMapper.rotateX(.2, .3, 90);
        double nextX = CoordinateMapper.rotateX(.4, .3, 90);
        double firstY = CoordinateMapper.rotateY(.2, .3, 90);
        double nextY = CoordinateMapper.rotateY(.4, .3, 90);
        if (firstX != nextX || nextY <= firstY) throw new AssertionError("Portrait vertical movement must not move the horizontal pointer");
        System.out.println("CoordinateMapperTest: all orientation checks passed");
    }
}
