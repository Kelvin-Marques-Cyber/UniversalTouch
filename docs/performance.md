# Desempenho e validação

Medições locais de 31/10/2026: Dell Inspiron 5567, openSUSE Leap 16, KDE/X11, tela 1366x768, Python 3.13, OpenCV 4.12, NumPy 2.2.6. Não existe garantia de consumo fixo entre computadores.

| Cenário | Memória residente |
|---|---:|
| Janela aberta, antes de usar a câmera | 32,5 MiB |
| Janela e câmera ativas, sem prévia | 114,0 MiB |
| Janela e câmera ativas, com prévia | 114,7 MiB |
| Tutorial interativo com gestos precisos, câmera e prévia | 114,2 MiB |
| Núcleo com imagem oficial de mão, 16 quadros | 93,8 MiB |
| Binário empacotado, benchmark com webcam (pico) | 101,6 MiB |

Benchmark de 12,22 segundos do binário: 116 quadros, 9,49 FPS, 12 quadros com mão reconhecida, mediana de inferência 82,45 ms; CPU equivalente a 105% de um núcleo (aproximadamente 26% de quatro núcleos lógicos). Esses números variam com a carga concorrente e não são promessa de latência. A medição lê /proc/self/status; o histórico de um lançador de processos não é contado como consumo do aplicativo.

Pausar desliga a webcam e remove o rastreador, mas o alocador das bibliotecas pode reter memória já reservada (103,7 MiB no ensaio após uso). Fechar encerra o processo e libera suas reservas. O teste confirmou que a thread da câmera termina ao pausar. O treino foi verificado com a câmera real e sem injetar eventos no desktop; o progresso foi testado com entradas determinísticas. A precisão dos gestos do usuário exige experimentação presencial.

O caminho desktop usa uma mão, modelos de aproximadamente 8 MB combinados, OpenCV CPU, uma imagem mais recente, 640x480 como teto de captura solicitado e até 15 inferências por segundo por padrão. A prévia gráfica está desligada inicialmente; câmera e rastreador só abrem ao iniciar.

`python -m universal_touch --benchmark 10` mede memória máxima residente, uso de CPU de um núcleo, quadros processados e mediana de inferência, sem injetar entrada. Esse teste não mede a qualidade dos gestos de uma pessoa. Para precisão, experimente cliques em alvos pequenos, arrasto e rolagem sob sua iluminação; ajuste espelhamento, distância e FPS conforme necessário.

Windows e Android precisam de teste físico com câmera, DPI, versões e permissões reais. A configuração de CI prevê testes de lógica e compilação, mas os jobs não iniciaram devido ao bloqueio da conta. Esta release inicial é uma prévia.

A suíte local atual passou 37 testes do aplicativo e 12 de distribuição. Inclui pinça mantida por 1,5 s enquanto a mão desloca 80 pixels (cursor imóvel, sem arrasto), clique único ao soltar, retorno sem salto, exclusão entre rolagem e clique, perda de mão e dados inválidos. No X11 real, os testes verificaram indicador nos cantos, passagem de cliques pelo indicador, minimizar uma janela própria e trocar entre as duas áreas já existentes, restaurando a área inicial. Isso verifica os contratos de controle; não mede a taxa de acerto dos gestos humanos.
