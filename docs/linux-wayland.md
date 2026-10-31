# Linux: X11 e Wayland

UniversalTouch detecta a sessão real. X11 usa XTest, sem privilégios administrativos. Atalhos globais e indicador discreto funcionam em X11 quando as extensões e atalhos estão disponíveis.

Em Wayland, mover o cursor de uma janela XWayland não controla o desktop inteiro. O adaptador usa um dispositivo de apontamento absoluto **uinput**, que exige permissão explícita. Instalação pelo código: `python -m pip install '.[wayland]'`. O pacote Linux de release inclui esse adaptador.

Caso queira habilitar uinput, um administrador pode instalar a regra fornecida:

```sh
sudo install -m 0644 packaging/70-universaltouch-uinput.rules /etc/udev/rules.d/70-universaltouch-uinput.rules
sudo modprobe uinput
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=misc
```

Se necessário, saia e entre novamente na sessão local. A regra utiliza `TAG+="uaccess"`: concede acesso ao usuário da sessão local ativa, sem tornar o dispositivo gravável por todos e sem conceder leitura de teclados. O comportamento de autorização depende de systemd-logind/udev da distribuição; confirme com seu administrador. Módulos devem ser carregados após reiniciar se a distribuição não fizer isso automaticamente.

Essa permissão permite que programas da sessão criem dispositivos de entrada. A instalação não executa os comandos automaticamente. Para remover, apague somente a regra criada acima e recarregue as regras; sair da sessão elimina permissões transitórias. Não use `chmod 666 /dev/uinput` nem conceda acesso geral ao grupo input.

Os gestos de três dedos para áreas de trabalho/minimizar dependem do gerenciador de janelas e estão implementados em X11 via EWMH/ICCCM. Nesta prévia, Wayland suporta mover/clicar/rolar, mas não esses atalhos.

No Wayland, use os botões da janela para iniciar/pausar; atalhos globais e posicionamento livre de sobreposições não são portáveis entre compositores. O ponteiro nativo do sistema indica a posição. Para uma experiência inicial completa com atalhos e indicador, escolha uma sessão X11 na tela de login quando ela estiver disponível.
