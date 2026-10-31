Prévia do UniversalTouch para PC: controle local por gestos da mão e tutorial interativo antes do primeiro uso.

- **Linux testado no PC:** x86-64, openSUSE Leap16/KDE/X11, glibc2.40+. Extraia a pasta inteira e execute `UniversalTouch`. Outras distribuições podem instalar pelo código; Wayland exige a configuração descrita no README.
- **Windows portátil, ainda sem teste em Windows:** x64, runtime Python oficial completo, Tcl/Tk, VC runtime, NumPy/OpenCV e modelos com hashes verificados. Extraia tudo e abra `Iniciar UniversalTouch.cmd`; `Diagnosticar.cmd` verifica os modelos. O nome do ZIP inclui `preview-untested`.
- **Tutorial:** mostra a webcam, ensina a posicionar a mão, mover o ponto até dois alvos e fazer uma pinça no alvo central. O treino não envia cliques para outros aplicativos. É possível repetir ou pular.
- **Recursos medidos no Linux:** aproximadamente 32,5 MiB antes de usar a câmera e 115 MiB com janela/tutorial ativos. Desempenho depende do hardware; veja `docs/performance.md`. Nenhum vídeo é salvo ou transmitido.
- **Verificação:** 22 testes do aplicativo passaram, incluindo eventos reais X11 e indicador nos cantos; 12 testes de ferramentas de distribuição passaram; inferência dos dois modelos e reconhecimento de uma imagem oficial com mão verificados. Câmera e pausa do tutorial foram testadas no PC.
- Código-fonte e SHA256SUMS incluídos. Android preservado como código experimental, sem APK nesta entrega a pedido do usuário.

O GitHub Actions não iniciou jobs por uma restrição de cobrança da conta. Esta release usa builds/verificações locais; não afirma validação de Windows, Wayland ou todas as distribuições. Aplicativos desktop não têm assinatura de produção.
