# Changelog

## 2.4 — 22/11/2026
- **Tela cheia**: toque num gráfico ou no painel de música (ou no botão novo na barra) para ver em tela cheia.
  Deslize para os lados para passar por Controles de música, GPU, CPU, RAM e FPS.
- Música em tela cheia: capa grande, tempo da faixa e botões grandes (aleatório, anterior, play/pause, próxima).
- Gráficos em tela cheia: número grande, máx / méd / mín (e 1% low no FPS), escala, linha da média, **1 min ou 5 min**
  e toque no gráfico para ler o valor de um momento.
- Ajustes › **Tela cheia**: escolha o que aparece e a ordem (também Temp. GPU e VRAM).
- A tela do iPhone não apaga enquanto a tela cheia está aberta (iOS 18.4+). Fecha no ✕ ou arrastando para baixo.
- **Deslizar para trocar de página** na grade de botões, com o botão cancelado se o gesto começar em cima dele.
  No PC, as setas ← → também trocam.
- O servidor guarda 5 minutos de histórico (antes, 2).

## 2.3 — 22/11/2026
- **FPS do jogo**: bloco novo na página PC com o FPS do jogo em primeiro plano, gráfico do último minuto,
  **máx / méd / mín** ao lado do número e **1% low** ao tocar. Mostra também o nome do jogo e o tempo de cada quadro.
- Usa o **PresentMon** (Intel, código aberto): o `iniciar.bat` baixa sozinho e pede uma vez para liberar a medição.
  A página do PC ganhou os botões **Baixar PresentMon** e **Liberar FPS**.
- Os gráficos largos (GPU, CPU, RAM, temperatura) também mostram **máx / méd / mín** o tempo todo.
- Clipe 30s e Explorador passaram para a página **Mais** para dar lugar ao FPS (cópia da organização anterior em `layout_v4_backup.json`).

## 2.2 — 22/11/2026
- **Botões maiores**: os botões foram reorganizados em três páginas (Principal, PC, Mais), com 3 colunas em pé e 5 deitado,
  sem rolar. Ficaram cerca de 30% maiores em pé e 40% maiores deitado, com mais espaço entre eles.
- **Toque à prova de engano**: aciona ao soltar o dedo; arrastar para fora cancela; segundo dedo é ignorado.
- **Segurar para acionar** (por botão), já ligado em Bloquear PC e Fechar janela.
- Ajustes › Toque: escolher entre "ao soltar" e "ao encostar".
- A troca de organização mantém os botões que você personalizou ou criou (cópia em `layout_v3_backup.json`).

## 2.1 — 22/11/2026
- **Jogos instalados**: novo tipo de botão que encontra o jogo no PC e abre pelo launcher certo
  (Epic Games, **EA app**, Steam ou atalhos do Windows). Os botões Fortnite, Rocket League e Battlefield 6 passam a usar isso.
- Editor com **lista de jogos e apps do PC**, com busca.
- Página do PC mostra os **jogos encontrados**.
- Corrigido: o quadrado **Adicionar** do modo edição não abria o editor.
- Corrigido: dois processos ligando ao mesmo tempo podiam falhar ao gravar o `settings.json`.

## 2.0 — 22/11/2026
- **Clipe com som**: o clipe dos últimos segundos agora grava o som do PC e o microfone (sem precisar de "Mixagem estéreo").
- **Gráficos ao vivo** de GPU, CPU, RAM, temperatura e VRAM (último minuto; toque para mín/méd/máx).
- **Painel do Spotify**: capa, música, artista, progresso, aleatório, anterior, play/pause e próxima.
- **Blocos de vários tamanhos** (1×1 até 4×2) com encaixe automático na grade.
- **Tela principal nova** com Spotify, gráficos, clipe, microfone e atalhos para Fortnite, Rocket League e Battlefield 6.
- **Temas**: Clássico, Minimal, Neon, Fofo, Liquid Glass e Gamer RGB, com modo claro, escuro ou automático.
- **Ícone na área de trabalho** e **início automático**: liga sozinho em segundo plano e avisa quando o cabo do iPhone conecta.
- Gravação do clipe só fica ativa com o celular conectado (economiza o PC).
- Barra de abas lateral com o celular deitado.
- `iniciar.bat` encontra o Python mesmo fora do PATH e oferece instalar se não houver.

## 1.0 — 22/11/2026
- Primeira versão: servidor Python + app web para iPhone, conexão por cabo USB (Ponto de Acesso) ou Wi-Fi,
  botões editáveis, mídia, microfone, atalhos, abrir programas, clipe dos últimos 15 s, uso de GPU/CPU/RAM.
