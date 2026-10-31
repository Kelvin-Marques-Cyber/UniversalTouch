// SPDX-License-Identifier: Apache-2.0
package org.universaltouch.android;

import java.util.ArrayList;
import java.util.List;

public final class FrameDispatcherTest {
    public static void main(String[] args) {
        List<GestureEngine.Frame> training = new ArrayList<>(), system = new ArrayList<>();
        GestureEngine.Frame click = new GestureEngine.Frame(); click.visible = true; click.click = true;
        new FrameDispatcher(true, training::add, system::add).send(click);
        if (training.size() != 1 || !system.isEmpty()) throw new AssertionError("Training clicks must remain entirely inside the training UI");
        new FrameDispatcher(false, training::add, system::add).send(click);
        if (system.size() != 1 || training.size() != 1) throw new AssertionError("A new control session must use only the control destination");
        System.out.println("FrameDispatcherTest: training safety checks passed");
    }
}
