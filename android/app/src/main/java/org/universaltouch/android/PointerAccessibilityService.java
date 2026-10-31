// SPDX-License-Identifier: Apache-2.0
package org.universaltouch.android;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.app.KeyguardManager;
import android.content.Intent;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
import android.os.SystemClock;
import android.util.DisplayMetrics;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.view.accessibility.AccessibilityEvent;

/** Does not inspect windows or nodes. Accessibility is used only for an overlay and gestures. */
public final class PointerAccessibilityService extends AccessibilityService {
    private static volatile PointerAccessibilityService instance;
    private final Handler main = new Handler(Looper.getMainLooper());
    private WindowManager windows;
    private PointerView pointer;
    private WindowManager.LayoutParams params;
    private final FrameMailbox mailbox = new FrameMailbox();
    private boolean gestureInFlight;
    private long lastScroll;

    public static boolean isConnected() { return instance != null; }
    public static void deliver(GestureEngine.Frame frame) {
        PointerAccessibilityService service = instance;
        if (service != null) service.enqueue(frame);
    }
    private void enqueue(GestureEngine.Frame frame) {
        if (!mailbox.offer(frame)) return;
        main.post(() -> {
            GestureEngine.Frame next = mailbox.poll(SystemClock.elapsedRealtime());
            if (next != null) render(next);
        });
    }
    public static void hide() {
        PointerAccessibilityService service = instance;
        if (service != null) service.main.post(() -> { if (service.pointer != null) service.pointer.setVisibility(View.INVISIBLE); });
    }
    @Override protected void onServiceConnected() {
        super.onServiceConnected();
        windows = (WindowManager) getSystemService(WINDOW_SERVICE);
        instance = this;
    }
    @Override public void onAccessibilityEvent(AccessibilityEvent event) { /* Never retrieve screen content. */ }
    @Override public void onInterrupt() { stopSession("Acessibilidade interrompida"); }
    @Override public boolean onUnbind(Intent intent) { stopSession("Acessibilidade desativada"); return super.onUnbind(intent); }
    @Override public void onDestroy() {
        instance = null;
        stopSession("Acessibilidade desativada");
        main.removeCallbacksAndMessages(null);
        if (pointer != null) { windows.removeView(pointer); pointer = null; }
        super.onDestroy();
    }
    private void stopSession(String reason) {
        if (CameraGestureService.running) {
            CameraGestureService.status = reason;
            stopService(new Intent(this, CameraGestureService.class));
        }
        if (pointer != null) pointer.setVisibility(View.INVISIBLE);
    }
    private void render(GestureEngine.Frame frame) {
        if (!CameraGestureService.running) { if (pointer != null) pointer.setVisibility(View.INVISIBLE); return; }
        KeyguardManager keyguard = (KeyguardManager) getSystemService(KEYGUARD_SERVICE);
        PowerManager power = (PowerManager) getSystemService(POWER_SERVICE);
        if (keyguard.isKeyguardLocked() || !power.isInteractive()) { stopSession("Parado: tela bloqueada"); return; }
        if (!frame.visible) { if (pointer != null) pointer.setVisibility(View.INVISIBLE); return; }
        DisplayMetrics metrics = new DisplayMetrics();
        windows.getDefaultDisplay().getRealMetrics(metrics);
        float px = (float) Math.max(1, Math.min(metrics.widthPixels - 2, frame.x * metrics.widthPixels));
        float py = (float) Math.max(1, Math.min(metrics.heightPixels - 2, frame.y * metrics.heightPixels));
        try {
            if (pointer == null) {
                pointer = new PointerView();
                int size = Math.round(36 * metrics.density);
                params = new WindowManager.LayoutParams(size, size, WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                        WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE | WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE |
                        WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                        PixelFormat.TRANSLUCENT);
                params.gravity = Gravity.TOP | Gravity.LEFT;
                if (Build.VERSION.SDK_INT >= 28) params.layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
                params.x = Math.round(px) - size / 2;
                params.y = Math.round(py) - size / 2;
                windows.addView(pointer, params);
            } else {
                params.x = Math.round(px) - params.width / 2;
                params.y = Math.round(py) - params.height / 2;
                windows.updateViewLayout(pointer, params);
            }
            pointer.armed = frame.armed;
            if (frame.click) pointer.flashUntil = SystemClock.uptimeMillis() + 180;
            pointer.setVisibility(View.VISIBLE);
            pointer.invalidate();
            if (frame.click) tap(px, py);
            else if (frame.scroll != 0 && SystemClock.uptimeMillis() - lastScroll > 450) {
                float startY = Math.max(metrics.heightPixels * .2f, Math.min(metrics.heightPixels * .8f, py));
                float endY = (float) Math.max(metrics.heightPixels * .12, Math.min(metrics.heightPixels * .88, startY + frame.scroll * metrics.heightPixels * 1.8));
                Path path = new Path(); path.moveTo(px, startY); path.lineTo(px, endY);
                if (send(path, 220)) lastScroll = SystemClock.uptimeMillis();
            }
        } catch (RuntimeException error) { stopSession("Falha no ponteiro. Reinicie o controle."); }
    }
    private void tap(float x, float y) { Path path = new Path(); path.moveTo(x, y); send(path, 70); }
    private boolean send(Path path, long duration) {
        if (gestureInFlight || !CameraGestureService.running) return false;
        GestureDescription gesture = new GestureDescription.Builder().addStroke(new GestureDescription.StrokeDescription(path, 0, duration)).build();
        gestureInFlight = true;
        boolean accepted = dispatchGesture(gesture, new GestureResultCallback() {
            @Override public void onCompleted(GestureDescription gestureDescription) { gestureInFlight = false; }
            @Override public void onCancelled(GestureDescription gestureDescription) { gestureInFlight = false; }
        }, main);
        if (!accepted) gestureInFlight = false;
        return accepted;
    }
    private final class PointerView extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private boolean armed;
        private long flashUntil;
        PointerView() { super(PointerAccessibilityService.this); setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO); }
        @Override protected void onDraw(Canvas canvas) {
            float cx = getWidth() / 2f, cy = getHeight() / 2f;
            float radius = getWidth() * .26f;
            paint.setStyle(Paint.Style.STROKE); paint.setStrokeWidth(getWidth() * .13f); paint.setColor(Color.BLACK);
            canvas.drawCircle(cx, cy, radius, paint);
            paint.setStrokeWidth(getWidth() * .07f);
            paint.setColor(SystemClock.uptimeMillis() < flashUntil ? Color.WHITE : armed ? Color.rgb(70,255,183) : Color.rgb(255,192,77));
            canvas.drawCircle(cx, cy, radius, paint);
            paint.setStyle(Paint.Style.FILL); canvas.drawCircle(cx, cy, getWidth() * .045f, paint);
        }
    }
}
