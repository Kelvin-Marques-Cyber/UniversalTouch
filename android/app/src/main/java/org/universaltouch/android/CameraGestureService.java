// SPDX-License-Identifier: Apache-2.0
package org.universaltouch.android;

import android.Manifest;
import android.app.KeyguardManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.graphics.Bitmap;
import android.graphics.ImageFormat;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.Image;
import android.media.ImageReader;
import android.os.Build;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.os.PowerManager;
import android.os.SystemClock;
import android.util.Range;
import android.util.Size;
import android.view.Surface;
import android.view.WindowManager;
import com.google.mediapipe.framework.image.BitmapImageBuilder;
import com.google.mediapipe.framework.image.MPImage;
import com.google.mediapipe.tasks.components.containers.NormalizedLandmark;
import com.google.mediapipe.tasks.core.BaseOptions;
import com.google.mediapipe.tasks.vision.core.ImageProcessingOptions;
import com.google.mediapipe.tasks.vision.core.RunningMode;
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarker;
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarkerResult;
import java.nio.ByteBuffer;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Collections;
import java.util.List;

/** One camera, one worker, two camera buffers, and no frame queue or recording. */
public final class CameraGestureService extends Service {
    public static final String ACTION_START = "org.universaltouch.android.START";
    public static final String ACTION_STOP = "org.universaltouch.android.STOP";
    public static volatile boolean running;
    public static volatile String status = "Parado · câmera liberada";
    private static final int NOTIFICATION_ID = 20;
    private final GestureEngine engine = new GestureEngine();
    private HandlerThread thread;
    private Handler worker;
    private final Handler main = new Handler(android.os.Looper.getMainLooper());
    private volatile boolean stopping;
    private CameraDevice camera;
    private CameraCaptureSession session;
    private ImageReader reader;
    private HandLandmarker detector;
    private Bitmap bitmap;
    private MPImage input;
    private int[] pixels;
    private final double[] uprightPoints = new double[42];
    private int sensorOrientation;
    private boolean front;
    private Range<Integer> fpsRange;
    private long lastAnalysis, lastImage;
    private SharedPreferences prefs;
    private final Runnable watchdog = new Runnable() {
        @Override public void run() {
            if (stopping) return;
            KeyguardManager lock = (KeyguardManager) getSystemService(KEYGUARD_SERVICE);
            PowerManager power = (PowerManager) getSystemService(POWER_SERVICE);
            if (!power.isInteractive() || lock.isKeyguardLocked()) { fail("Parado: tela bloqueada"); return; }
            if (!PointerAccessibilityService.isConnected()) { fail("Parado: acessibilidade desativada"); return; }
            if (SystemClock.elapsedRealtime() - lastImage > 8000) { fail("A câmera não respondeu. Tente iniciar novamente."); return; }
            main.postDelayed(this, 1000);
        }
    };
    private final BroadcastReceiver screenOff = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) { fail("Parado: tela bloqueada"); }
    };

    @Override public void onCreate() {
        super.onCreate();
        prefs = getSharedPreferences("control", MODE_PRIVATE);
        thread = new HandlerThread("UniversalTouch-camera"); thread.start(); worker = new Handler(thread.getLooper());
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(screenOff, new IntentFilter(Intent.ACTION_SCREEN_OFF), Context.RECEIVER_NOT_EXPORTED);
        else registerReceiver(screenOff, new IntentFilter(Intent.ACTION_SCREEN_OFF));
    }
    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent == null || ACTION_STOP.equals(intent.getAction())) { status = "Parado pelo usuário · câmera liberada"; stopSelf(); return START_NOT_STICKY; }
        if (!ACTION_START.equals(intent.getAction()) || running) return START_NOT_STICKY;
        KeyguardManager lock = (KeyguardManager) getSystemService(KEYGUARD_SERVICE);
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED ||
                !PointerAccessibilityService.isConnected() || lock.isKeyguardLocked()) {
            status = "Ative a acessibilidade e permita a câmera antes de iniciar."; stopSelf(); return START_NOT_STICKY;
        }
        try {
            Notification notification = createNotification();
            if (Build.VERSION.SDK_INT >= 30) startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_CAMERA);
            else startForeground(NOTIFICATION_ID, notification);
            running = true;
            status = "Iniciando câmera…";
            lastImage = SystemClock.elapsedRealtime();
            main.postDelayed(watchdog, 1000);
            worker.post(this::initialize);
        } catch (RuntimeException error) { fail("Não foi possível iniciar a câmera. Tente com o aplicativo aberto."); }
        return START_NOT_STICKY;
    }
    private Notification createNotification() {
        String channelId = "gesture-control";
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(channelId, "Controle por gestos", NotificationManager.IMPORTANCE_LOW);
            channel.setDescription("Sessão de câmera iniciada por você. Use Parar para encerrar.");
            ((NotificationManager) getSystemService(NOTIFICATION_SERVICE)).createNotificationChannel(channel);
        }
        PendingIntent open = PendingIntent.getActivity(this, 0, new Intent(this, MainActivity.class), PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        PendingIntent stop = PendingIntent.getService(this, 1, new Intent(this, CameraGestureService.class).setAction(ACTION_STOP), PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        Notification.Builder builder = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(this, channelId) : new Notification.Builder(this);
        return builder.setSmallIcon(R.drawable.ic_hand).setContentTitle("UniversalTouch · câmera ativa")
                .setContentText("Controle local por gestos. Toque em Parar para encerrar.")
                .setContentIntent(open).setOngoing(true).setOnlyAlertOnce(true)
                .addAction(new Notification.Action.Builder(null, "Parar", stop).build()).build();
    }
    private void initialize() {
        if (stopping) return;
        try {
            BaseOptions base = BaseOptions.builder().setModelAssetPath("hand_landmarker.task").build();
            detector = HandLandmarker.createFromOptions(this, HandLandmarker.HandLandmarkerOptions.builder()
                    .setBaseOptions(base).setRunningMode(RunningMode.VIDEO).setNumHands(1)
                    .setMinHandDetectionConfidence(.6f).setMinHandPresenceConfidence(.6f).setMinTrackingConfidence(.6f).build());
            if (stopping) return;
            CameraManager manager = (CameraManager) getSystemService(CAMERA_SERVICE);
            String selected = null;
            boolean rear = prefs.getBoolean("rear", false);
            for (String id : manager.getCameraIdList()) {
                Integer facing = manager.getCameraCharacteristics(id).get(CameraCharacteristics.LENS_FACING);
                if (selected == null) selected = id;
                if (facing != null && facing == (rear ? CameraCharacteristics.LENS_FACING_BACK : CameraCharacteristics.LENS_FACING_FRONT)) { selected = id; break; }
            }
            if (selected == null) throw new IllegalStateException("No camera");
            CameraCharacteristics characteristics = manager.getCameraCharacteristics(selected);
            Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);
            front = facing != null && facing == CameraCharacteristics.LENS_FACING_FRONT;
            Integer orientation = characteristics.get(CameraCharacteristics.SENSOR_ORIENTATION);
            sensorOrientation = orientation == null ? 0 : orientation;
            StreamConfigurationMap map = characteristics.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
            if (map == null) throw new IllegalStateException("No camera outputs");
            Size[] sizes = map.getOutputSizes(ImageFormat.YUV_420_888);
            if (sizes == null || sizes.length == 0) throw new IllegalStateException("No YUV output");
            Size size = Arrays.stream(sizes).filter(s -> s.getWidth() <= 640 && s.getHeight() <= 480)
                    .max(Comparator.comparingInt(s -> s.getWidth() * s.getHeight())).orElseThrow(() -> new IllegalStateException("Camera has no low-memory output"));
            Range<Integer>[] ranges = characteristics.get(CameraCharacteristics.CONTROL_AE_AVAILABLE_TARGET_FPS_RANGES);
            if (ranges != null) fpsRange = Arrays.stream(ranges).filter(r -> r.getLower() <= 15 && r.getUpper() >= 15)
                    .min(Comparator.comparingInt((Range<Integer> r) -> r.getUpper().intValue())).orElse(null);
            reader = ImageReader.newInstance(size.getWidth(), size.getHeight(), ImageFormat.YUV_420_888, 2);
            bitmap = Bitmap.createBitmap(size.getWidth(), size.getHeight(), Bitmap.Config.ARGB_8888);
            // MPImage owns this bitmap and recycles it on close. Keep both until teardown.
            input = new BitmapImageBuilder(bitmap).build();
            pixels = new int[size.getWidth() * size.getHeight()];
            reader.setOnImageAvailableListener(this::analyzeLatest, worker);
            if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) { fail("Permissão de câmera revogada."); return; }
            manager.openCamera(selected, new CameraDevice.StateCallback() {
                @Override public void onOpened(CameraDevice device) {
                    if (stopping) { device.close(); return; }
                    camera = device; createCaptureSession();
                }
                @Override public void onDisconnected(CameraDevice device) { device.close(); fail("Câmera desconectada. Controle encerrado."); }
                @Override public void onError(CameraDevice device, int error) { device.close(); fail("Falha na câmera. Feche outros aplicativos de câmera e tente novamente."); }
            }, worker);
        } catch (Exception error) { fail("Não foi possível preparar a câmera ou o modelo. Reinicie o controle."); }
    }
    private void createCaptureSession() {
        try {
            camera.createCaptureSession(Collections.singletonList(reader.getSurface()), new CameraCaptureSession.StateCallback() {
                @Override public void onConfigured(CameraCaptureSession configured) {
                    if (stopping || camera == null) { configured.close(); return; }
                    session = configured;
                    try {
                        CaptureRequest.Builder request = camera.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
                        request.addTarget(reader.getSurface());
                        request.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_VIDEO);
                        if (fpsRange != null) request.set(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE, fpsRange);
                        session.setRepeatingRequest(request.build(), null, worker);
                        status = "Câmera ativa · mostre uma mão aberta";
                    } catch (Exception error) { fail("Falha ao capturar imagens. Controle encerrado."); }
                }
                @Override public void onConfigureFailed(CameraCaptureSession configured) { fail("Câmera incompatível com esta configuração."); }
            }, worker);
        } catch (Exception error) { fail("Falha ao abrir a sessão da câmera."); }
    }
    private void analyzeLatest(ImageReader source) {
        if (stopping) return;
        try (Image image = source.acquireLatestImage()) {
            if (image == null) return;
            long now = SystemClock.elapsedRealtime(); lastImage = now;
            if (now - lastAnalysis < 67) return;
            lastAnalysis = now;
            convertYuv(image);
            int rotation = rotationDegrees();
            {
                HandLandmarkerResult result = detector.detectForVideo(input, ImageProcessingOptions.builder().setRotationDegrees(rotation).build(), now);
                engine.setSmoothing(.06 + prefs.getInt("smoothing", 25) * .004);
                if (result.landmarks().isEmpty()) {
                    PointerAccessibilityService.deliver(engine.update(now, false, 0, 0, 0, false));
                    status = "Câmera ativa · mão não encontrada";
                    return;
                }
                List<NormalizedLandmark> points = result.landmarks().get(0);
                double aspect = rotation % 180 == 0 ? (double) bitmap.getWidth() / bitmap.getHeight() : (double) bitmap.getHeight() / bitmap.getWidth();
                if (points.size() != 21) throw new IllegalStateException("Unexpected landmark count");
                for (int i = 0; i < 21; i++) {
                    NormalizedLandmark p = points.get(i);
                    uprightPoints[i * 2] = CoordinateMapper.rotateX(p.x(), p.y(), rotation);
                    uprightPoints[i * 2 + 1] = CoordinateMapper.rotateY(p.x(), p.y(), rotation);
                }
                double palm = Math.max(.03, distance(5, 17, aspect));
                double pinch = distance(4, 8, aspect) / palm;
                boolean scrollPose = extended(8, 6, aspect) && extended(12, 10, aspect) &&
                        !extended(16, 14, aspect) && !extended(20, 18, aspect);
                // Mirror only after rotating the raw camera coordinates into upright orientation.
                double x = front ? 1 - uprightPoints[16] : uprightPoints[16];
                double gain = 1.15 + prefs.getInt("gain", 50) * .012;
                x = .5 + (x - .5) * gain;
                double y = .5 + (uprightPoints[17] - .5) * gain;
                GestureEngine.Frame frame = engine.update(now, true, x, y, pinch, scrollPose);
                PointerAccessibilityService.deliver(frame);
                status = scrollPose ? "Rolagem · mova dois dedos" : frame.armed ? "Pronto · una polegar e indicador para tocar" : "Abra a mão para armar o toque";
            }
        } catch (Exception error) { fail("Falha ao analisar a mão. Controle encerrado; câmera liberada."); }
    }
    private boolean extended(int tip, int joint, double aspect) {
        return distance(tip, 0, aspect) > distance(joint, 0, aspect) * 1.17;
    }
    private double distance(int a, int b, double aspect) {
        return Math.hypot((uprightPoints[a * 2] - uprightPoints[b * 2]) * aspect,
                uprightPoints[a * 2 + 1] - uprightPoints[b * 2 + 1]);
    }
    private int rotationDegrees() {
        int display = ((WindowManager) getSystemService(WINDOW_SERVICE)).getDefaultDisplay().getRotation();
        int degrees = display == Surface.ROTATION_90 ? 90 : display == Surface.ROTATION_180 ? 180 : display == Surface.ROTATION_270 ? 270 : 0;
        return front ? (sensorOrientation + degrees) % 360 : (sensorOrientation - degrees + 360) % 360;
    }
    private void convertYuv(Image image) {
        Image.Plane[] planes = image.getPlanes();
        ByteBuffer y = planes[0].getBuffer(), u = planes[1].getBuffer(), v = planes[2].getBuffer();
        int width = image.getWidth(), height = image.getHeight();
        for (int row = 0; row < height; row++) {
            int yr = row * planes[0].getRowStride();
            int ur = (row / 2) * planes[1].getRowStride();
            int vr = (row / 2) * planes[2].getRowStride();
            for (int col = 0; col < width; col++) {
                int yy = (y.get(yr + col * planes[0].getPixelStride()) & 255) - 16;
                int uu = (u.get(ur + (col / 2) * planes[1].getPixelStride()) & 255) - 128;
                int vv = (v.get(vr + (col / 2) * planes[2].getPixelStride()) & 255) - 128;
                int luminance = 1192 * Math.max(0, yy);
                int red = Math.max(0, Math.min(255, (luminance + 1634 * vv) >> 10));
                int green = Math.max(0, Math.min(255, (luminance - 833 * vv - 400 * uu) >> 10));
                int blue = Math.max(0, Math.min(255, (luminance + 2066 * uu) >> 10));
                pixels[row * width + col] = 0xff000000 | (red << 16) | (green << 8) | blue;
            }
        }
        bitmap.setPixels(pixels, 0, width, 0, 0, width, height);
    }
    private void fail(String reason) { status = reason; main.post(this::stopSelf); }
    @Override public void onDestroy() {
        stopping = true;
        running = false;
        PointerAccessibilityService.hide();
        main.removeCallbacksAndMessages(null);
        unregisterReceiver(screenOff);
        stopForeground(true);
        worker.post(() -> {
            if (session != null) { session.close(); session = null; }
            if (camera != null) { camera.close(); camera = null; }
            if (reader != null) { reader.close(); reader = null; }
            if (detector != null) { detector.close(); detector = null; }
            if (input != null) { input.close(); input = null; }
            bitmap = null;
            pixels = null; engine.reset(); thread.quitSafely();
        });
        if (status.startsWith("Câmera") || status.startsWith("Pronto") || status.startsWith("Abra") || status.startsWith("Rolagem") || status.startsWith("Iniciando")) status = "Parado · câmera liberada";
        super.onDestroy();
    }
    @Override public IBinder onBind(Intent intent) { return null; }
}
