# UniversalTouch Implementation Plan

**Goal:** Controle por webcam instalado e projeto multiplataforma publicado com releases de prévia.
**Architecture:** Processamento local com fila limitada; adaptadores de entrada separados da interpretação dos gestos. Interface nativa leve; Android nativo independente.
**Tech Stack:** Python/Tk/OpenCV; Java/Android/MediaPipe; GitHub Actions/PyInstaller.
**Spec:** docs/design.md

## Constraints
- Preservar Apache-2.0; não incorporar código AGPL do Mudra.
- Webcam 640x480, uma mão, <=15 FPS e duas threads como padrão.
- Início pausado, sem autostart, sem frames gravados/transmitidos.
- Botões soltos em pausa, mão perdida, erro e encerramento.
- Releases representam plataformas compiladas; documentar hardware não testado.

## Tasks
- [x] Desktop: escrever e executar testes RED; implementar máquina de gestos e adaptadores X11/Win32/uinput; validar suíte GREEN.
- [x] Desktop: interface e indicador, comandos de diagnóstico/benchmark; inferência real e eventos numa janela própria; instalar atalhos.
- [ ] Android (delegado, arquivos android/): detector, acessibilidade, câmera em primeiro plano, ponteiro, testes e APK.
- [x] Distribuição (delegado, arquivos scripts/, packaging/, .github/): modelos com hashes, pacotes/CI/releases.
- [ ] Integração: revisar código e permissões; rodar suíte/builds, medir recursos, publicar commit/tag e acompanhar CI até os artefatos.

## Review focus
Pausa com arrasto; dados inválidos; retorno da mão com pinça fechada; escala de DPI/monitores; revogação de câmera/acessibilidade. Testes cobrem os três primeiros; teste local de integração cobre monitor único X11; CI e instruções separam compilação de testes em hardware.
