# Textos prontos para publicar no GitHub

## Nome do repositório
`phonedeck`

## Descrição (campo "About" do repositório)
> Transforme o iPhone num Stream Deck do PC pelo cabo USB ou Wi-Fi, sem App Store: botões editáveis, clipe dos últimos 15 s com som e microfone, FPS do jogo e gráficos de GPU/CPU/RAM, painel do Spotify e 6 temas.

## Tópicos (Topics)
```
stream-deck  streamdeck  iphone  ios  pwa  windows  python  aiohttp  websocket
macropad  replay-buffer  ffmpeg  spotify  gaming  hardware-monitor  fps-counter  presentmon  obs  pt-br
```

## Imagem de prévia (Social preview)
Em **Settings › General › Social preview**, envie `docs/screenshots/social-preview.png` (1280×640).

---

## Como publicar

### Opção A: pelo site (sem instalar nada)
1. Em <https://github.com/new>, crie o repositório `phonedeck` (público), **sem** README, .gitignore ou licença (o projeto já tem os três).
2. Na página do repositório vazio, clique em **uploading an existing file**.
3. Arraste **o conteúdo** da pasta `PhoneDeck` (não a pasta em si). **Não envie** `settings.json`, `layout.json`, `phonedeck.log` nem a pasta `.venv`, se existirem.
4. Escreva a mensagem "Primeira versão" e clique em **Commit changes**.

### Opção B: pelo terminal (Git)
```bash
cd PhoneDeck
git init
git add .
git commit -m "PhoneDeck 2.6"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/phonedeck.git
git push -u origin main
```
O `.gitignore` já impede que o seu `settings.json` (com o código de acesso) seja enviado.

### Criar a versão (Release)
Em **Releases › Draft a new release**: tag `v2.6`, título `PhoneDeck 2.6`, e cole o texto abaixo.
Anexe um `.zip` do projeto, para quem não usa Git.

---

## Texto da Release v2.6

**PhoneDeck 2.6: o seu iPhone como Stream Deck do PC** 🎛️

Novidades:
- 🎬 **Clipe dos últimos 15 s com som do PC + microfone**
- 🎯 **FPS do jogo** com gráfico, máx, méd, mín e 1% low (qualquer jogo, sem sobreposição na tela)
- 📈 **Gráficos ao vivo** de GPU, CPU e RAM (último minuto)
- 🖥️ **Tela cheia** deslizante com música, GPU, CPU, RAM e FPS
- 🖱️ **Mouse e teclado**: o celular vira touchpad e teclado do PC
- 📌 **Botões fixos** em todas as páginas (Clipe 15s sempre à mão)
- 🎵 **Painel do Spotify** com capa, aleatório, anterior, play/pause e próxima
- 🎮 Botões prontos para **Fortnite, Rocket League e Battlefield 6**, que acham o jogo na Epic, EA app ou Steam
- 👆 **Botões grandes**, toque à prova de engano e páginas que trocam deslizando
- 🎨 **6 temas** (Clássico, Minimal, Neon, Fofo, Liquid Glass, Gamer RGB), claro/escuro/automático
- 🧩 Blocos de vários tamanhos com encaixe automático
- 🔌 **Ícone na área de trabalho** e **liga sozinho ao conectar o cabo do iPhone**

**Como instalar:** baixe o `.zip`, rode o `iniciar.bat` e escaneie o QR code com o iPhone.
Guia completo: `docs/GUIA.md`, no próprio repositório.

Requisitos: Windows 10/11, iPhone com iOS 16 ou mais novo, ffmpeg (para o clipe).
