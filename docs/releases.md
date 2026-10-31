# Builds e releases

As instruções reproduzíveis de empacotamento estão em [packaging/README.md](../packaging/README.md).

Tags `v*` executam os testes e builds Windows/Linux no GitHub Actions. A publicação automática só ocorre após todos os jobs exigidos passarem. O Android é opcional por execução manual e não bloqueia a entrega desktop.

O GitHub Actions da conta retornou um bloqueio de cobrança antes de iniciar qualquer etapa. A prévia 0.1.0 é publicada com verificações locais: Linux nativo do PC disponível (glibc2.40) e Windows portátil montado com runtime oficial e wheels verificadas. O ZIP Windows ainda não foi executado em Windows; isso aparece no nome do artefato e nas instruções. A matriz de CI permanece pronta para validação futura após desbloqueio da conta. Nenhum APK é distribuído nesta entrega focada no PC.

Os pacotes incluem os modelos, licenças e SHA256SUMS.txt. Modelos têm hashes fixos e versões registradas. O ZIP/tar deve ser extraído inteiro antes de abrir a aplicação. Pacotes Linux oficiais usam o glibc mínimo documentado, enquanto o pacote construído localmente no openSUSE Leap16 é identificado separadamente por glibc2.40.

Compilação e autotestes não comprovam qualidade em toda câmera, fabricante, compositor ou versão do sistema. Limitações e medições estão em [performance.md](performance.md).
