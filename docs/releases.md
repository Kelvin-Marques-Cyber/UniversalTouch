# Builds e releases

As instruções reproduzíveis de empacotamento estão em [packaging/README.md](../packaging/README.md).

Tags `v*` executam os testes e builds Windows/Linux/Android no GitHub Actions. A publicação só ocorre após todos os jobs exigidos passarem. A release inicial 0.1.0 é uma prévia; o APK usa assinatura de desenvolvimento na ausência de chave de produção, conforme indicado no nome e na documentação.

Os pacotes incluem os modelos, licenças e SHA256SUMS.txt. Modelos têm hashes fixos e versões registradas. O ZIP/tar deve ser extraído inteiro antes de abrir a aplicação. Pacotes Linux oficiais usam o glibc mínimo documentado, enquanto o pacote construído localmente no openSUSE Leap16 é identificado separadamente por glibc2.40.

Compilação e autotestes não comprovam qualidade em toda câmera, fabricante, compositor ou versão do sistema. Limitações e medições estão em [performance.md](performance.md).
