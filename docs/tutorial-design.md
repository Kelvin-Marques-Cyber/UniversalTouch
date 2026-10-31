# Tutorial desktop

Pedido: tutorial interativo antes do primeiro uso, porque o usuário não conseguia identificar como começar. Foco atual: PC. Android foi retirado da entrega prioritária pelo usuário; o código já criado é preservado como experimental.

Referência principal: interface nativa existente UniversalTouch. Preservar fundo #101820, texto legível claro, fonte do sistema, verde #65e5d3 para cursor/estado, azul #68b8ff para alvo de treino. Sem mídia pesada nem browser embutido.

Pesquisa Refero: ferramentas de estilos/telas/fluxos retornaram NO_SUBSCRIPTION. Fallback de pesquisa: guias locais refero-design/references/craft-details.md, copywriting.md e typography.md. Aplicados: labels concretos de ação, erros com próximo passo, estado de carregamento explícito, foco de teclado preservado, dimensões reservadas para prévia, uma hierarquia curta de texto e fonte do sistema para evitar custo extra.

Decisões: três etapas com progresso visível, treino responde a gestos reais (restrição do usuário); prévia pequena com marcadores para dar retorno sobre enquadramento; alvo com cor distinta do cursor; iniciar câmera só por botão; botão pausar disponível e Esc; treino não possui adaptador de entrada do sistema; fechar tutorial não marca concluído; conclusão ou Pular por enquanto registram preferência; sempre oferecer Repetir no painel principal. Tutorial bloqueia iniciar controle real por botão ou atalho enquanto aberto.

Validação: testes de armar, passar pelos dois alvos, clique novo no alvo, perda de mão, preferências inválidas e persistência; teste real de câmera e ciclo de vida; renderização em tela 1366x768 do usuário antes de empacotar.

Revisão de usabilidade: o usuário confirmou indicador sozinho para mover, polegar/indicador para clicar e indicador/médio juntos para rolar. Tutorial e controle real usam o mesmo PreciseController; primeira etapa arma com indicador, segunda visita alvos, terceira ensina pinça com cursor congelado e clique ao soltar. A conclusão apresenta rolagem e atalhos de três dedos. Preferência de tutorial versão 3 reapresenta o treino após a mudança dos gestos. Prévia opcional fica em janela separada para não cortar os controles em telas menores; velocidade ajustável pausa o controle antes da alteração. O indicador branco completo sinaliza a pinça reconhecida.
