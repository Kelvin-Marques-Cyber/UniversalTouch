# UniversalTouch

Controle local por gestos da mão, usando uma webcam comum. Interface nativa leve para **Windows e Linux**, com tutorial interativo no primeiro uso. Projeto Apache-2.0. O código Android é experimental e foi preservado; a entrega atual tem foco no PC.

**Prévia 0.1.0:** modelos executam localmente; nenhum vídeo é salvo ou enviado. O consumo depende da câmera, do processador e do sistema. Consulte [medições e validação](docs/performance.md) antes de comparar requisitos. Precisão e iluminação precisam ser avaliadas no seu hardware.

## Baixar

[Releases Windows e Linux](https://github.com/Kelvin-Marques-Cyber/UniversalTouch/releases).

- Windows 10/11 x64: extraia o ZIP completo e abra `Iniciar UniversalTouch.cmd`. O pacote de prévia inclui Python oficial e dependências; ainda não foi executado em Windows. Pacotes nativos `UniversalTouch.exe` também podem ser gerados pelo CI quando disponível.
- Linux x86_64: extraia o pacote e execute `UniversalTouch/UniversalTouch`. A prévia construída no openSUSE Leap 16 exige glibc 2.40 ou posterior. Para outras distribuições, use a instalação pelo código abaixo; o perfil CI prevê glibc 2.35. KDE/GNOME X11 são o caminho mais simples. Para Wayland, veja [permissão de entrada](docs/linux-wayland.md).

Se o pacote indicar assinatura de desenvolvimento, ele é uma **prévia para testes**, não uma versão assinada para produção. Mantenha todos os arquivos extraídos juntos. Releases binárias Linux têm o glibc mínimo do ambiente de build; outras distribuições podem instalar pelo código.

## Usar no PC

1. Abra UniversalTouch. No primeiro uso, o **tutorial interativo** abre com a câmera desligada. Clique em **Começar treino**, abra a mão, leve o ponto verde aos dois alvos e pratique uma pinça no alvo central. Os gestos do tutorial ficam dentro da janela.
2. Conclua o tutorial e clique em **Iniciar gestos**, ou pressione **Ctrl+Alt+G**. O botão **Aprender os gestos** permite repetir o treino; **Pular por enquanto** leva ao painel sem treinamento.
3. Mostre a mão aberta por um instante para armar o controle. Use um fundo simples e iluminação frontal.
4. Mova o indicador para posicionar o cursor. O indicador discreto é opcional; a prévia de vídeo vem desligada para reduzir trabalho.

| Gesto | Ação no desktop |
|---|---|
| Indicador apontando | Mover o cursor com suavização |
| Polegar + indicador | Pressionar botão esquerdo; solte para concluir o clique |
| Manter a pinça por mais de 0,3 s | Arrastar |
| Polegar + médio | Clique direito, uma vez por pinça |
| Indicador e médio erguidos, outros dois recolhidos | Rolar movendo os dedos verticalmente |
| Punho fechado ou mão fora da imagem | Soltar botões e parar; abra a mão para retomar |

**Ctrl+Alt+G** inicia/pausa. **Ctrl+Alt+Shift+G** encerra. **Esc** pausa quando a janela está em foco. Atalhos globais dependem de X11/Windows e podem estar ocupados por outro aplicativo; nesses casos, use a janela. Wayland oferece os controles da janela e o cursor nativo, com limitações de sobreposição.

Pausar desliga a câmera e descarrega o rastreador. Fechar encerra o processo. Não há inicialização automática, serviço oculto, treinamento de modelo, PyTorch, Electron ou acesso à Internet durante o uso. Um monitor sem sensor continua sem toque físico: a webcam interpreta **gestos no ar**.

## Instalar pelo código

Precisa de Python 3.10–3.13, Tk e ambiente virtual. Debian/Ubuntu: `python3-venv python3-tk`; Fedora: `python3 python3-tkinter`; openSUSE: Python e seu pacote tkinter; Arch: `python tk`. A câmera e as bibliotecas gráficas do sistema precisam estar funcionais.

```sh
git clone https://github.com/Kelvin-Marques-Cyber/UniversalTouch.git
cd UniversalTouch
python3 -m venv .venv
.venv/bin/python scripts/fetch_models.py
.venv/bin/python -m pip install .
.venv/bin/python -m universal_touch
```

No Windows, use `py -3 -m venv .venv`, substitua `.venv/bin/python` por `.venv\Scripts\python.exe` e execute os mesmos comandos. O Python do instalador oficial inclui Tk. Para desenvolver a partir de uma instalação editável, use `pip install -e .`.

## Verificar e medir

```sh
python -m universal_touch --self-test
python -m unittest discover -s tests -v
python -m unittest discover -s scripts/tests -v
python -m universal_touch --benchmark 10
```

O autoteste roda ambos os modelos em pixels sintéticos, sem câmera nem entrada. O benchmark usa a webcam, não controla o mouse nem grava imagens. `--fps 10` reduz processamento; o padrão é até 15 FPS com duas threads e uma imagem mais recente, sem fila crescente. A velocidade da câmera pode limitar o resultado.

## Desenvolver e distribuir

[Arquitetura](docs/design.md) · [plano](docs/implementation-plan.md) · [builds e releases](docs/releases.md) · [privacidade](PRIVACY.md) · [créditos e licenças](NOTICE).

O CI foi configurado para testar o núcleo em Windows/Linux e gerar pacotes nativos. O GitHub Actions está bloqueado por uma restrição da conta; esta prévia usa builds e verificações locais. O Android só é compilado por execução manual opcional. Compilação bem-sucedida não substitui testes com câmera e permissões em cada aparelho. A prévia não promete operar em telas de bloqueio, aplicativos elevados, áreas protegidas ou interfaces que neguem entrada de acessibilidade.
