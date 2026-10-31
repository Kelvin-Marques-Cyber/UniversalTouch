# UniversalTouch 0.1

Controle local por gestos, com prioridade para baixo consumo, precisão do cursor e encerramento simples. Windows e Linux têm aplicativo desktop; Android tem aplicativo nativo para controlar o próprio aparelho. O usuário autorizou implementação, instalação no próprio PC e publicação neste repositório e em releases.

O repositório já usa Apache-2.0. Preservamos essa licença: o desktop usa diretamente modelos e exemplos Apache-2.0 do OpenCV Zoo. Mudra foi pesquisado como referência, mas seu código AGPL não integra o produto. Consideradas: aplicação Electron (memória desnecessária), pacote MediaPipe completo/Qt (mais dependências), OpenCV headless/Tk (escolhido no desktop), Android nativo/MediaPipe (escolhido no celular).

Desktop: Python 3.10+, Tk, OpenCV headless, NumPy; uma mão, imagem limitada a 640x480, até 15 inferências/s, até duas threads, fila de um quadro. O modelo é carregado ao iniciar; pausa solta botões e fecha câmera. Interface inicia pausada, prévia de vídeo é opcional. O cursor do sistema e um indicador opcional mostram a posição. Pinça indicador/polegar faz clique/arrasto; médio/polegar faz clique direito; dois dedos rolam; punho solta botões e exige rearmar com mão aberta. Perda de rastreio ou erro nunca deixa botão pressionado.

Windows usa Win32; Linux X11 usa XTest. Wayland exige uinput com autorização de usuário ativo, pois XTest não controla janelas nativas Wayland. Não expandir permissões para teclado bruto nem tornar uinput gravável por todos. A interface explica indisponibilidade em vez de prometer compatibilidade automática. Linux binário depende do glibc mínimo do builder; instalação pelo código atende outras distribuições compatíveis.

Android: câmera frontal, MediaPipe para uma mão, serviço de câmera em primeiro plano iniciado por ação explícita, notificação com Parar, serviço de acessibilidade ativado manualmente para executar toques e indicador. Sem permissão de Internet, sem captura de conteúdo de outras aplicações, sem armazenamento de imagens. Parar deve liberar câmera, modelo e sobreposição. APK sem chave de produção é identificado como prévia assinada para testes, nunca anunciado como assinatura de produção.

Distribuição: builds verificáveis no CI para Windows, Linux e APK; release inicial prévia 0.1.0 com hashes e limitações explícitas. Medir RAM/CPU/FPS no PC disponível; não extrapolar para aparelhos não medidos nem chamar compilação de validação funcional nesses aparelhos.

Verificação: testes de estados de gestos, perda de mão, pausa, dados inválidos, uma ação por pinça, rolagem; inferência real na webcam sem salvar imagens; teste X11 em janela própria; smoke da interface; build APK e testes Android; CI Windows/Linux. A validação presencial do usuário em cada hardware permanece necessária.
