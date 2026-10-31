// SPDX-License-Identifier: Apache-2.0
package org.universaltouch.android;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.provider.Settings;
import android.view.View;
import android.view.WindowInsets;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.Switch;
import android.widget.TextView;

public final class MainActivity extends Activity {
    private TextView status;
    private Button start;
    private Button cameraPermission;
    private boolean startAfterNotification;
    private final Handler handler = new Handler();
    private final Runnable refresh = new Runnable() {
        @Override public void run() {
            if (status != null) {
                status.setText(CameraGestureService.status + "\nAcessibilidade: " +
                        (PointerAccessibilityService.isConnected() ? "ativada" : "desativada"));
                start.setEnabled(!CameraGestureService.running);
                boolean cameraGranted = checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED;
                cameraPermission.setText(cameraGranted ? "2  ·  Câmera permitida" : "2  ·  Permitir câmera");
                cameraPermission.setEnabled(!cameraGranted);
            }
            handler.postDelayed(this, 600);
        }
    };

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (!getSharedPreferences("control", MODE_PRIVATE).getBoolean("tutorialSeen", false)) {
            startActivity(new Intent(this, TutorialActivity.class));
            finish();
            return;
        }
        SharedPreferences prefs = getSharedPreferences("control", MODE_PRIVATE);
        ScrollView scroll = new ScrollView(this);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(24);
        content.setPadding(pad, pad, pad, pad);
        scroll.addView(content);
        scroll.setOnApplyWindowInsetsListener((view, insets) -> {
            if (Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars());
                view.setPadding(bars.left, bars.top, bars.right, bars.bottom);
            } else {
                view.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                        insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            }
            return insets;
        });
        addText(content, "UniversalTouch", 31, Color.WHITE);
        addText(content, "SEU ANDROID, NAS SUAS MÃOS", 12, Color.rgb(96,227,186));
        addText(content, "Mova um ponteiro e toque na tela usando a câmera frontal. Tudo é processado neste aparelho.", 17, Color.LTGRAY);
        addButton(content, "Aprender com treino guiado", view -> startActivity(new Intent(this, TutorialActivity.class)));
        status = addText(content, "Pronto para configurar", 16, Color.rgb(96,227,186));
        addButton(content, "1  ·  Ativar acessibilidade", view -> discloseAccessibility());
        cameraPermission = addButton(content, "2  ·  Permitir câmera", view -> requestCamera());
        addText(content, "3  ·  Ajuste antes de iniciar", 18, Color.WHITE);
        Switch rear = new Switch(this);
        rear.setText("Usar câmera traseira");
        rear.setChecked(prefs.getBoolean("rear", false));
        rear.setOnCheckedChangeListener((button, checked) -> prefs.edit().putBoolean("rear", checked).apply());
        content.addView(rear);
        slider(content, "Suavização (esquerda = mais precisão)", "smoothing", 25, prefs);
        slider(content, "Alcance (direita = menos movimento da mão)", "gain", 50, prefs);
        start = addButton(content, "Iniciar controle", view -> startControl());
        addButton(content, "Parar e liberar câmera", view -> {
            stopService(new Intent(this, CameraGestureService.class));
            CameraGestureService.status = "Parado pelo usuário";
        });
        addText(content, "COMO USAR", 14, Color.rgb(96,227,186));
        addText(content, "• Apoie o celular e mantenha uma mão visível, com boa iluminação.\n\n" +
                "• A ponta do indicador move o ponteiro. Abra a mão por um instante para armar o clique: o ponteiro fica verde.\n\n" +
                "• Una polegar e indicador por um instante para tocar. Solte antes de cada novo toque.\n\n" +
                "• Para rolar, estenda indicador e médio; dobre anelar e mínimo. Mova a mão para cima ou para baixo.\n\n" +
                "• O controle para ao bloquear a tela. Use Parar no aplicativo ou na notificação para encerrar.", 16, Color.LTGRAY);
        addText(content, "PRIVACIDADE E ACESSO", 14, Color.rgb(96,227,186));
        addText(content, "A câmera funciona somente durante uma sessão iniciada por você. O serviço de acessibilidade desenha o ponteiro e envia toques e rolagens sobre outros aplicativos. Não lê textos nem conteúdo das janelas. Não há gravação, transmissão, conta, anúncios ou permissão de internet.\n\n" +
                "Desative o serviço nas configurações de acessibilidade quando não precisar dele. Algumas telas protegidas impedem toques automáticos.\n\n" +
                "Versão inicial · Requer Android 7 ou posterior. Desempenho depende do aparelho; até 15 análises por segundo, uma mão e imagem de até 640 × 480.", 14, Color.LTGRAY);
        setContentView(scroll);
    }

    private void discloseAccessibility() {
        new AlertDialog.Builder(this).setTitle("Controle sobre a tela")
                .setMessage(getString(org.universaltouch.android.R.string.accessibility_description))
                .setNegativeButton("Agora não", null)
                .setPositiveButton("Abrir configurações", (dialog, which) -> startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))).show();
    }
    private void requestCamera() {
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{Manifest.permission.CAMERA}, 10);
        else if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED &&
                !getSharedPreferences("control", MODE_PRIVATE).getBoolean("notificationAsked", false)) {
            getSharedPreferences("control", MODE_PRIVATE).edit().putBoolean("notificationAsked", true).apply();
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 11);
        }
    }
    private void startControl() {
        if (!PointerAccessibilityService.isConnected()) { discloseAccessibility(); return; }
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) { requestCamera(); return; }
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED &&
                !getSharedPreferences("control", MODE_PRIVATE).getBoolean("notificationAsked", false)) {
            startAfterNotification = true;
            requestCamera();
            return;
        }
        try {
            Intent intent = new Intent(this, CameraGestureService.class).setAction(CameraGestureService.ACTION_START);
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(intent); else startService(intent);
        } catch (RuntimeException error) {
            CameraGestureService.status = "Não foi possível iniciar. Abra o aplicativo e tente novamente.";
        }
    }
    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (requestCode == 11 && startAfterNotification) {
            startAfterNotification = false;
            startControl();
        }
    }
    @Override protected void onResume() { super.onResume(); if (status != null) handler.post(refresh); }
    @Override protected void onPause() { handler.removeCallbacks(refresh); super.onPause(); }
    private TextView addText(LinearLayout parent, String text, int size, int color) {
        TextView label = new TextView(this);
        label.setText(text); label.setTextSize(size); label.setTextColor(color);
        label.setPadding(0, dp(8), 0, dp(12)); parent.addView(label); return label;
    }
    private Button addButton(LinearLayout parent, String text, View.OnClickListener listener) {
        Button button = new Button(this); button.setText(text); button.setAllCaps(false);
        button.setOnClickListener(listener); parent.addView(button, new LinearLayout.LayoutParams(-1, dp(56))); return button;
    }
    private void slider(LinearLayout parent, String title, String key, int initial, SharedPreferences prefs) {
        addText(parent, title, 14, Color.LTGRAY);
        SeekBar bar = new SeekBar(this); bar.setMax(100); bar.setProgress(prefs.getInt(key, initial));
        bar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) { if (fromUser) prefs.edit().putInt(key, progress).apply(); }
            @Override public void onStartTrackingTouch(SeekBar seekBar) { }
            @Override public void onStopTrackingTouch(SeekBar seekBar) { }
        }); parent.addView(bar);
    }
    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
}
