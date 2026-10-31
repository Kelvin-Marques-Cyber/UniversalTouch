// SPDX-License-Identifier: Apache-2.0
package org.universaltouch.android;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/** Safe, local practice. No accessibility permission or injected Android gestures are used. */
public final class TutorialActivity extends Activity {
    private final Handler handler = new Handler();
    private final TutorialProgress progress = new TutorialProgress();
    private TextView instruction, feedback;
    private Button cameraPermission, finish;
    private PracticeView practice;
    private boolean practicing, paused;
    private final Runnable refresh = new Runnable() {
        @Override public void run() {
            if (!practicing) {
                if (cameraPermission != null) {
                    boolean granted = cameraGranted();
                    cameraPermission.setText(granted ? "✓ Câmera já permitida" : "Permitir a câmera");
                    cameraPermission.setEnabled(!granted);
                }
            } else {
                TrainingBridge.Sample sample = TrainingBridge.latest;
                if (sample != null) {
                    progress.update(sample.frame);
                    practice.sample = sample;
                    practice.invalidate();
                    if (!sample.frame.visible) feedback.setText("Ainda não vi sua mão. Afaste-a um pouco e deixe os dedos dentro da câmera frontal.");
                    else feedback.setText(sample.frame.armed ? "Mão encontrada · ponteiro verde: toque pronto" : "Mão encontrada · abra a mão para deixar o ponteiro verde");
                } else feedback.setText(CameraGestureService.status);
                if (progress.phase() == 0) instruction.setText("2 de 4 · Mostre a mão aberta\nOlhe a câmera frontal. Mantenha a mão inteira visível até o ponteiro ficar verde.");
                else if (progress.phase() == 1) instruction.setText("3 de 4 · Mova o indicador\nLeve o ponteiro até o alvo e segure um instante. Alvos: " + progress.targetsCompleted() + "/3.");
                else if (progress.phase() == 2) instruction.setText("4 de 4 · Faça seu primeiro toque\nMire no alvo central. Abra a mão para armar; una polegar e indicador por um instante, depois solte.");
                else {
                    instruction.setText("Você conseguiu!\nSeu movimento e seu toque foram reconhecidos pela câmera.");
                    feedback.setText("O treino só reagiu dentro deste aplicativo. Para controlar o Android, você ativará a acessibilidade manualmente na próxima tela.");
                    finish.setEnabled(true);
                }
                if (!CameraGestureService.running && sample != null) {
                    feedback.setText(CameraGestureService.status + "\nToque em Reiniciar treino para tentar novamente.");
                }
            }
            handler.postDelayed(this, 80);
        }
    };
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        stopService(new Intent(this, CameraGestureService.class));
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        showSetup(false);
    }
    private boolean cameraGranted() { return checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED; }
    private LinearLayout page() {
        ScrollView scroll = new ScrollView(this);
        LinearLayout column = new LinearLayout(this); column.setOrientation(LinearLayout.VERTICAL);
        column.setPadding(dp(22), dp(16), dp(22), dp(22)); scroll.addView(column);
        scroll.setOnApplyWindowInsetsListener((view, insets) -> {
            if (Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars());
                view.setPadding(bars.left, bars.top, bars.right, bars.bottom);
            } else view.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(), insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            return insets;
        });
        setContentView(scroll); return column;
    }
    private void showSetup(boolean resumed) {
        cameraPermission = null;
        LinearLayout column = page();
        text(column, "Vamos aprender juntos", 29, Color.WHITE);
        text(column, resumed ? "TREINO PAUSADO · CÂMERA LIBERADA" : "1 DE 4 · PREPARAR O CELULAR", 12, mint());
        text(column, "Você vai mover um ponteiro e acertar alvos com sua mão, aqui mesmo. O treino não toca em outros aplicativos e ainda não precisa de acessibilidade.", 17, Color.LTGRAY);
        text(column, "1. Apoie o celular em pé, com a câmera frontal virada para você.\n\n2. Ilumine sua mão. Comece com ela inteira na frente da câmera, a cerca de um braço de distância.\n\n3. Deixe o indicador apontado para cima. Abra a mão e mova devagar; aproxime ou afaste até ela aparecer no desenho ao vivo.", 16, Color.LTGRAY);
        cameraPermission = button(column, cameraGranted() ? "✓ Câmera já permitida" : "Permitir a câmera", view -> {
            if (!cameraGranted()) requestPermissions(new String[]{Manifest.permission.CAMERA}, 30);
        });
        cameraPermission.setEnabled(!cameraGranted());
        text(column, cameraGranted() ? "A câmera já está autorizada. Nenhuma janela de permissão precisa aparecer de novo." : "O Android pedirá sua autorização. As imagens ficam neste aparelho e não são gravadas.", 14, mint());
        button(column, resumed ? "Retomar treino seguro" : "Começar treino seguro", view -> beginPractice());
        button(column, "Pular por enquanto", view -> leaveTutorial());
    }
    private void beginPractice() {
        if (!cameraGranted()) { requestPermissions(new String[]{Manifest.permission.CAMERA}, 30); return; }
        TrainingBridge.foreground = true;
        TrainingBridge.latest = null;
        practicing = true; paused = false; cameraPermission = null;
        LinearLayout column = page();
        text(column, "Treino com a sua mão", 27, Color.WHITE);
        text(column, "SEGURO · TOQUES SÓ DENTRO DO TREINO", 11, mint());
        instruction = text(column, "2 de 4 · Mostre a mão aberta\nMantenha a mão inteira na câmera frontal.", 18, Color.WHITE);
        practice = new PracticeView();
        column.addView(practice, new LinearLayout.LayoutParams(-1, -2));
        feedback = text(column, "Abrindo a câmera…", 14, mint());
        finish = button(column, "Concluir e abrir controles", view -> leaveTutorial()); finish.setEnabled(progress.phase() == 3);
        button(column, "Reiniciar câmera do treino", view -> {
            stopService(new Intent(this, CameraGestureService.class)); practicing = false; showSetup(true);
        });
        button(column, "Pular por enquanto", view -> leaveTutorial());
        Intent intent = new Intent(this, CameraGestureService.class).setAction(CameraGestureService.ACTION_TRAIN);
        try { if (Build.VERSION.SDK_INT >= 26) startForegroundService(intent); else startService(intent); }
        catch (RuntimeException error) { practicing = false; showSetup(true); }
    }
    private void leaveTutorial() {
        TrainingBridge.foreground = false;
        practicing = false;
        stopService(new Intent(this, CameraGestureService.class));
        getSharedPreferences("control", MODE_PRIVATE).edit().putBoolean("tutorialSeen", true).apply();
        startActivity(new Intent(this, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP)); finish();
    }
    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (requestCode == 30) showSetup(false);
    }
    @Override protected void onResume() {
        super.onResume(); TrainingBridge.foreground = true;
        if (paused) { paused = false; showSetup(true); }
        handler.post(refresh);
    }
    @Override protected void onPause() {
        TrainingBridge.foreground = false;
        paused = practicing;
        practicing = false;
        handler.removeCallbacks(refresh);
        stopService(new Intent(this, CameraGestureService.class));
        super.onPause();
    }
    @Override public void onBackPressed() { leaveTutorial(); }
    private TextView text(LinearLayout parent, String value, int size, int color) {
        TextView t = new TextView(this); t.setText(value); t.setTextSize(size); t.setTextColor(color);
        t.setPadding(0, dp(7), 0, dp(9)); parent.addView(t); return t;
    }
    private Button button(LinearLayout parent, String label, View.OnClickListener action) {
        Button b = new Button(this); b.setText(label); b.setAllCaps(false); b.setOnClickListener(action);
        parent.addView(b, new LinearLayout.LayoutParams(-1, dp(52))); return b;
    }
    private int mint() { return Color.rgb(96,227,186); }
    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    private final class PracticeView extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private TrainingBridge.Sample sample;
        private final int[][] bones = {{0,1},{1,2},{2,3},{3,4},{0,5},{5,6},{6,7},{7,8},{5,9},{9,10},{10,11},{11,12},{9,13},{13,14},{14,15},{15,16},{13,17},{0,17},{17,18},{18,19},{19,20}};
        PracticeView() { super(TutorialActivity.this); setContentDescription("Área de treino controlada apenas pelos gestos da câmera"); }
        @Override protected void onMeasure(int width, int height) {
            int size = Math.min(MeasureSpec.getSize(width), dp(330)); setMeasuredDimension(MeasureSpec.getSize(width), size);
        }
        @Override protected void onDraw(Canvas canvas) {
            float w = getWidth(), h = getHeight(); canvas.drawColor(Color.rgb(22,44,51));
            float x = (float) progress.targetX() * w, y = (float) progress.targetY() * h;
            paint.setColor(mint()); paint.setStyle(Paint.Style.STROKE); paint.setStrokeWidth(dp(2));
            if (progress.phase() == 1 || progress.phase() == 2) {
                canvas.drawOval(x - .13f*w, y - .13f*h, x + .13f*w, y + .13f*h, paint);
                canvas.drawLine(x-dp(7), y, x+dp(7), y, paint); canvas.drawLine(x,y-dp(7),x,y+dp(7),paint);
            }
            paint.setStyle(Paint.Style.FILL); paint.setTextSize(dp(13)); paint.setColor(Color.LTGRAY);
            canvas.drawText(progress.phase() == 0 ? "Mostre sua mão à câmera frontal" : progress.phase() == 3 ? "✓ Movimento e toque reconhecidos" : "Mova o ponteiro até o alvo", dp(10), h-dp(14), paint);
            if (sample == null || !sample.frame.visible) return;
            if (sample.points != null) {
                float preview = Math.min(w*.32f, dp(110));
                float ox = w-preview-dp(5), oy = dp(5);
                paint.setColor(Color.rgb(107,146,157)); paint.setStrokeWidth(dp(1));
                for (int[] bone : bones) canvas.drawLine(ox+(float)sample.points[bone[0]*2]*preview,oy+(float)sample.points[bone[0]*2+1]*preview,ox+(float)sample.points[bone[1]*2]*preview,oy+(float)sample.points[bone[1]*2+1]*preview,paint);
                for (int i=0;i<21;i++) canvas.drawCircle(ox+(float)sample.points[i*2]*preview,oy+(float)sample.points[i*2+1]*preview,dp(2),paint);
            }
            paint.setColor(sample.frame.armed ? mint() : Color.rgb(255,192,77));
            canvas.drawCircle((float)sample.frame.x*w,(float)sample.frame.y*h,dp(9),paint);
            paint.setColor(Color.BLACK);canvas.drawCircle((float)sample.frame.x*w,(float)sample.frame.y*h,dp(2),paint);
        }
    }
}
