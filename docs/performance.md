# Desempenho e validação

As medições reais desta prévia serão registradas aqui após os testes no PC disponível. Não existe garantia de consumo fixo entre computadores ou versões do Android.

O caminho desktop usa uma mão, modelos de aproximadamente 8 MB combinados, OpenCV CPU, uma imagem mais recente, 640x480 como teto de captura solicitado e até 15 inferências por segundo por padrão. A prévia gráfica está desligada inicialmente; câmera e rastreador só abrem ao iniciar.

`python -m universal_touch --benchmark 10` mede memória máxima residente, uso de CPU de um núcleo, quadros processados e mediana de inferência, sem injetar entrada. Esse teste não mede a qualidade dos gestos de uma pessoa. Para precisão, experimente cliques em alvos pequenos, arrasto e rolagem sob sua iluminação; ajuste espelhamento, distância e FPS conforme necessário.

Windows e Android precisam de teste físico com câmera, DPI, versões e permissões reais. CI cobre testes de lógica e compilação; não constitui validação em todos os dispositivos. Esta release inicial é uma prévia.
