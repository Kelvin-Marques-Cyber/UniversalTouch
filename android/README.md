# UniversalTouch para Android

Aplicativo nativo, offline, para controlar **o próprio Android** por uma mão na câmera. Não é um controle remoto de computador. Requer Android 7 (API 24) ou posterior e processador ARM de 32 ou 64 bits.

## Uso

1. Instale o APK. Em instalações externas à Play Store, o Android pode exigir que você permita configurações restritas nas informações do aplicativo antes de habilitar a acessibilidade.
2. Abra UniversalTouch, leia a divulgação e habilite manualmente seu serviço nas configurações de acessibilidade.
3. Permita o uso da câmera; permita notificações para ter acesso ao botão **Parar**.
4. Apoie o aparelho, ilumine a mão e toque em **Iniciar controle**. Você pode abrir outros aplicativos enquanto a sessão continua.
5. Mova o indicador para apontar. Abra a mão por cerca de 300 ms para armar o toque (ponteiro verde); una polegar e indicador por cerca de 120 ms para tocar uma vez. Separe os dedos antes do próximo toque.
6. Para rolar, estenda indicador e médio, dobre os demais e mova a mão verticalmente. A pose deve permanecer estável antes de iniciar a rolagem.
7. Pare pelo aplicativo ou pela notificação. Bloquear a tela, desativar a acessibilidade ou uma falha na câmera também encerra a sessão. Não reinicia sozinho.

A suavização e o alcance podem ser ajustados antes ou durante a sessão. Mais suavização significa resposta mais lenta e menos tremor. O alcance maior permite cobrir a tela com menos movimento. A câmera frontal tem o eixo horizontal espelhado para um controle intuitivo; há opção para câmera traseira.

## Privacidade e limites

- Não solicita permissão de internet, armazenamento, áudio, captura de tela ou inicialização automática.
- Não grava imagens. MediaPipe roda localmente, em CPU, com uma mão e no máximo 15 análises/s.
- Camera2 usa uma saída YUV de até 640 × 480, dois buffers da câmera, um bitmap reutilizável e uma única execução de inferência. Frames antigos são descartados; a entrega ao ponteiro guarda o movimento mais recente e no máximo uma ação recente. Ações antigas são descartadas e perder a mão cancela ações pendentes.
- O serviço de acessibilidade não lê textos, nós ou conteúdo das janelas. Usa `TYPE_ACCESSIBILITY_OVERLAY` para um pequeno ponteiro sem interceptar toques e `dispatchGesture` para toques e rolagens.
- Algumas telas protegidas e alguns aplicativos podem recusar gestos. O sistema pode encerrar a sessão por limites do aparelho. A versão inicial precisa de validação física em diferentes fabricantes; o consumo real de RAM e a precisão dependem do hardware, luz e posição da mão.
- O modelo MediaPipe e suas bibliotecas nativas têm custo de memória próprio. O projeto limita os buffers e a taxa de análise, mas não promete um limite de RAM sem medição no aparelho.

## Build e verificações

Requisitos: JDK 17, Android SDK plataforma 36 e build-tools 36.0.0. O wrapper fixa Gradle 9.3.1, com checksum, e o plugin Android é 9.1.0.

```sh
cd android
./gradlew --no-daemon :app:gestureTest :app:lintRelease :app:assembleRelease
```

O APK fica em `app/build/outputs/apk/release/app-release.apk`. Sem configuração de assinatura, é uma **prévia assinada com chave de desenvolvimento**, com identificador `org.universaltouch.android.preview` e versão `0.1.0-preview`. Cada máquina tem sua chave de desenvolvimento; para atualizar uma instalação, use a mesma chave ou desinstale a prévia anterior.

Uma distribuição de produção requer uma chave mantida fora do repositório. Configure `ANDROID_KEYSTORE_PATH`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS` e `ANDROID_KEY_PASSWORD`; o build usa essa assinatura e o identificador de produção `org.universaltouch.android`. Nunca envie a chave ou senhas ao Git.

`gestureTest` executa testes Java independentes de Android: bloqueio de pinça no início, armar por tempo, clique único por pinça, novo clique após soltar, desarmar ao perder a mão, suavização, retomada sem posição antiga rolagem sem clique, preservação de ações recentes e mapeamento de orientação em 0/90/180/270 graus. Para executar sem o SDK:

```sh
mkdir -p /tmp/universaltouch-tests
javac -d /tmp/universaltouch-tests app/src/main/java/org/universaltouch/android/GestureEngine.java app/src/main/java/org/universaltouch/android/FrameMailbox.java app/src/main/java/org/universaltouch/android/CoordinateMapper.java app/src/gestureTest/java/org/universaltouch/android/*.java
java -cp /tmp/universaltouch-tests org.universaltouch.android.AllTests
```

O build baixa o [modelo oficial do Google, versão 1](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task) e verifica SHA-256 `fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1`. O modelo fica em um asset ignorado pelo Git e é incluído no APK. O aplicativo não faz downloads. O manifesto remove explicitamente a permissão de internet transitiva do MediaPipe, bloqueando também a transmissão de métricas da biblioteca.

## Dependências e referências

Código do aplicativo sob Apache-2.0, conforme a licença na raiz do projeto. Usa MediaPipe Tasks Vision 0.10.35 e o modelo Hand Landmarker do Google. Consulte as licenças e avisos de terceiros incluídos nas dependências; o modelo vem do projeto MediaPipe, sob Apache-2.0.

- [Hand Landmarker para Android — Google](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/android)
- [MediaPipe — código e licença Apache-2.0](https://github.com/google-ai-edge/mediapipe)
- [AccessibilityService e dispatchGesture — Android](https://developer.android.com/reference/android/accessibilityservice/AccessibilityService)
- [Serviços de câmera em primeiro plano — Android](https://developer.android.com/develop/background-work/services/fgs/service-types#camera)
