# PhoneDeck — seu iPhone como Stream Deck do PC

O PhoneDeck transforma o celular num painel de botões totalmente configurável para o PC (Windows 10/11).
Ele tem duas partes:

* **Servidor no PC** (Python): recebe os toques e executa as ações no Windows.
* **App no iPhone** (web app): abre pelo Safari e vira um ícone na Tela de Início, em tela cheia.
  Não precisa de App Store, Mac nem conta de desenvolvedor.

A ligação pode ser **pelo cabo USB** (pelo Ponto de Acesso Pessoal do iPhone) ou **pelo Wi-Fi**.

### O que já vem pronto

| Botão | O que faz |
|---|---|
| Clipe 15s / 30s | Salva os **últimos 15 (ou 30) segundos da tela** em `Vídeos\PhoneDeck` |
| GPU / CPU / RAM | Mostradores ao vivo com % de uso (atualizam a cada segundo) |
| Temp. GPU / VRAM | Temperatura e memória de vídeo (placas NVIDIA) |
| Play/Pause, Próxima, Anterior | Controle de música (Spotify, YouTube, qualquer player) |
| Vol + / Vol − / Mudo | Volume do Windows (o botão fica vermelho quando está mudo) |
| Microfone | Muta/desmuta o microfone do Windows (fica vermelho quando mutado) |
| Área de trabalho | Mostra a área de trabalho (Win+D) |
| Print, Gerenciador, Fechar janela, Mutar Discord… | Atalhos de teclado |
| Navegador, Explorador, Spotify, Calculadora | Abrem programas ou sites |
| Digitar texto, Bloquear PC, Meus clipes | Digita um texto, bloqueia o PC, abre a pasta dos clipes |

Tudo pode ser trocado: nome, ícone (ou emoji), cor, ação, posição, páginas e número de colunas.

---

## 1. Instalação no PC (uma vez só)

1. **Instale o Python 3** (3.10 ou mais novo): https://www.python.org/downloads/
   Na instalação, marque **"Add python.exe to PATH"**.
   (Ou no terminal: `winget install --id Python.Python.3.12 -e`)
2. **Instale o ffmpeg** (necessário só para o botão de clipe). No terminal:
   ```
   winget install --id Gyan.FFmpeg -e
   ```
3. **Para usar o cabo USB:** instale o app **Dispositivos Apple** (Microsoft Store) ou o **iTunes**.
   Eles trazem o driver que faz o Windows enxergar a rede do iPhone pelo cabo.
4. Descompacte a pasta `PhoneDeck` onde quiser e dê dois cliques em **`iniciar.bat`**.
   Na primeira vez ele instala as bibliotecas (1–2 minutos).
5. Se o **Firewall do Windows** perguntar, permita em redes **Privadas e Públicas**.
   A rede do cabo do iPhone costuma ser classificada como "Pública".

Quando o servidor sobe, o navegador do PC abre uma página com **QR codes** para conectar.

## 2. Conectar o iPhone

### Pelo cabo USB (recomendado)

1. No iPhone: **Ajustes › Ponto de Acesso Pessoal › Permitir Outros Conectarem** (ligado).
2. Conecte o cabo no PC e toque em **Confiar** no iPhone, se ele perguntar.
3. Recarregue a página de QR code no PC (F5). Deve aparecer o cartão verde **"Cabo USB"**
   (um endereço tipo `172.20.10.x`).
4. Aponte a câmera do iPhone para esse QR code e abra o link no Safari.

> O Ponto de Acesso precisa estar disponível no seu plano de celular. Se a opção estiver
> cinza, use o Wi-Fi (abaixo). Funciona igual.

**Dica para não gastar seus dados móveis:** com o cabo, o Windows pode achar que o iPhone é
uma "internet" e mandar tráfego por ele. Para o PC continuar usando sua internet normal,
abra o PowerShell **como administrador** e rode (troque o nome pelo que aparecer no primeiro comando, algo como "Ethernet 3"):
```powershell
Get-NetAdapter | Where-Object InterfaceDescription -like "*Apple*"
Set-NetIPInterface -InterfaceAlias "Ethernet 3" -InterfaceMetric 500
```

### Pelo Wi-Fi

Com o PC e o iPhone na **mesma rede**, escaneie o QR code do cartão "Rede: …".

### Instalar como app na Tela de Início

No Safari, toque em **Compartilhar › Adicionar à Tela de Início**.
A partir daí, abra o PhoneDeck pelo ícone: ele abre em tela cheia, sem barras do Safari, e já
guarda o código de acesso.

**Para a tela não apagar:** Ajustes › Tela e Brilho › Bloqueio Automático › **Nunca**
(com o cabo, o iPhone fica carregando enquanto isso).

## 3. Editar os botões

* Toque no **lápis** (canto superior direito) para entrar no modo edição.
* Toque em qualquer botão para mudar **nome, ação, ícone e cor**, mover para os lados, duplicar ou excluir.
* **Adicionar** (último quadrado) cria um botão novo.
* **＋** na barra de abas cria uma página nova. Toque na aba atual para renomear, mover ou excluir a página.
* O ícone de **ajustes** (ao lado do ✓) muda o número de colunas (em pé e deitado), mostra/esconde os nomes
  e restaura os botões padrão.
* Toque no **✓** para sair da edição. Tudo é salvo automaticamente no PC (`layout.json`).

Você também pode editar pelo PC: abra `http://localhost:8765` no navegador. No campo de atalho há um botão
de teclado: clique nele e pressione o atalho que quer gravar.

### Tipos de ação

| Ação | Exemplo / observação |
|---|---|
| Mídia / volume | play/pause, próxima, anterior, parar, vol +, vol −, mudo |
| Mutar microfone | alterna o microfone padrão do Windows |
| Atalho de teclado | `ctrl+shift+m`, `alt+f10`, `win+g`, sequência: `ctrl+c, alt+tab, ctrl+v` |
| Clipe da tela | segundos (até o tamanho do buffer, padrão 30 s) |
| Mostrar área de trabalho | Win+D |
| Abrir programa, pasta ou site | `https://twitch.tv`, `C:\Program Files\obs-studio\bin\64bit\obs64.exe`, `spotify:`, `discord:`, `steam://open/main`, `%USERPROFILE%\Downloads` |
| Rodar comando | `shutdown /s /t 60` (desliga em 1 min), qualquer comando do cmd |
| Digitar texto | digita no programa em foco (aceita acentos e emoji) |
| Mostrador ao vivo | GPU, temperatura da GPU, VRAM, CPU, RAM, volume, relógio |
| Ir para outra página | navegação entre páginas |
| Abrir pasta de clipes / Bloquear o PC / Nada | — |

Nomes de teclas aceitos: `ctrl shift alt win`, `a–z`, `0–9`, `f1–f24`, `enter esc tab space backspace delete insert home end pageup pagedown up down left right printscreen pause capslock`, `num0–num9`, `add subtract multiply divide`, `playpause nexttrack prevtrack volumeup volumedown volumemute`.

## 4. Clipe dos últimos segundos

Por padrão o PhoneDeck grava a tela **em segundo plano** com o ffmpeg, em pedaços de 2 s numa pasta
temporária que se sobrescreve (não enche o disco). Ao tocar no botão, ele junta os últimos N segundos num `.mp4`
em `Vídeos\PhoneDeck`.

* Captura pela GPU (Desktop Duplication), leve e funciona com jogos em janela/tela cheia sem bordas.
* Codifica na placa de vídeo quando possível (NVIDIA → AMD → Intel → CPU), escolhido sozinho.
* A bolinha no canto do botão de clipe mostra o estado: **verde** gravando, **amarela** iniciando, **vermelha** erro.

**Já usa NVIDIA Instant Replay, Xbox Game Bar ou o Replay Buffer do OBS?** Mude o modo para "atalho"
no `settings.json` e o botão só aperta o atalho deles (eles também gravam o som):
```json
"clip": { "mode": "hotkey", "hotkey": "alt+f10" }
```
(`alt+f10` = NVIDIA; `win+alt+g` = Xbox Game Bar; no OBS use o atalho que você definiu para "Salvar replay".)

**Som no clipe (opcional):** o modo ffmpeg grava só a imagem. Para incluir o som do PC, ative a "Mixagem estéreo"
nas configurações de som do Windows e coloque o nome exato do dispositivo em `audio_device`.
Para ver os nomes: `ffmpeg -list_devices true -f dshow -i dummy`.

## 5. Arquivo `settings.json`

Criado na primeira execução, na pasta do PhoneDeck. Feche o PhoneDeck antes de editar.

| Campo | Padrão | Para que serve |
|---|---|---|
| `port` | 8765 | Porta do servidor |
| `token` | aleatório | Código de acesso do celular |
| `require_token` | true | Exige o código (deixe ligado) |
| `open_browser_on_start` | true | Abre a página de QR code ao iniciar |
| `ffmpeg_path` | "" | Caminho do ffmpeg.exe, se não estiver no PATH |
| `clip.mode` | "ffmpeg" | `ffmpeg`, `hotkey` ou `off` |
| `clip.buffer_seconds` | 30 | Quantos segundos ficam guardados (máx. 300) |
| `clip.fps` | 30 | Quadros por segundo do clipe |
| `clip.capture` | "auto" | `auto`, `ddagrab` (GPU) ou `gdigrab` (compatível) |
| `clip.monitor` | 0 | Qual monitor gravar (0 = principal) |
| `clip.encoder` | "auto" | `auto`, `h264_nvenc`, `h264_amf`, `h264_qsv`, `libx264` |
| `clip.bitrate` | "8M" | Qualidade do vídeo (aumente para 12M–20M em 1440p/4K) |
| `clip.audio_device` | "" | Dispositivo de som (ver acima) |
| `clip.hotkey` | "alt+f10" | Atalho usado no modo `hotkey` |
| `clip.output_dir` | "" | Pasta dos clipes (vazio = Vídeos\PhoneDeck) |

## 6. Problemas comuns

| Problema | Solução |
|---|---|
| Não aparece o cartão "Cabo USB" | Ligue o Ponto de Acesso **antes** de conectar o cabo; confira se tem o app Dispositivos Apple/iTunes; troque de porta/cabo; recarregue a página (F5). |
| O iPhone abre o link mas fica "Procurando o PC…" | É o Firewall: Painel de Controle › Firewall do Windows › Permitir um aplicativo › marque **Python** em Privada **e** Pública. |
| Pede código de acesso | Digite o código que aparece na janela preta do PhoneDeck no PC. |
| Atalhos não funcionam dentro de um jogo/programa | Se o programa roda como administrador, rode o `iniciar.bat` como administrador também. |
| Botão de clipe com bolinha vermelha | ffmpeg não instalado ou falhou. Veja `%TEMP%\phonedeck_buffer\ffmpeg_log.txt`. Tente `"capture": "gdigrab"`. |
| GPU mostra "—" | Placas NVIDIA mostram tudo. AMD/Intel mostram só o uso %, e só no Windows 10 (1709) ou mais novo. |
| O endereço do Wi-Fi mudou | Escaneie o QR de novo (ou use o cabo, cujo endereço é sempre parecido). |

**Iniciar junto com o Windows:** aperte Win+R, digite `shell:startup`, Enter, e crie ali um atalho para o
`iniciar.bat`. Coloque `"open_browser_on_start": false` no `settings.json` para não abrir o navegador toda vez.

**Gerar um .exe:** depois de rodar o `iniciar.bat` uma vez, rode `criar_exe.bat`. O arquivo sai em `dist\PhoneDeck.exe`.

## 7. Como o projeto é organizado (para quem quiser mexer)

```
PhoneDeck/
├─ iniciar.bat          inicia tudo (cria o ambiente na 1ª vez)
├─ criar_exe.bat        gera um PhoneDeck.exe (opcional)
├─ requirements.txt     bibliotecas Python
├─ servidor/
│  ├─ main.py           servidor web + WebSocket, página de QR code
│  ├─ actions.py        executa cada tipo de ação  ← adicione ações novas aqui
│  ├─ winkeys.py        teclado (SendInput do Windows)
│  ├─ audio.py          microfone e volume (Core Audio)
│  ├─ stats.py          CPU, RAM e GPU (NVML / contadores do Windows)
│  ├─ clipper.py        gravação contínua e corte do clipe (ffmpeg)
│  └─ config.py         settings.json, layout.json e botões padrão
└─ web/                 app do celular (HTML/CSS/JS puro, sem dependências)
   ├─ index.html, style.css, app.js, icons.js
```

**Criar um tipo de ação novo:** (1) trate o `type` novo em `servidor/actions.py`;
(2) adicione o nome em `ACTION_TYPES` no `config.py`; (3) adicione a opção na lista `ACTIONS`
e os campos em `renderParams()` no `web/app.js`.

**Protocolo (WebSocket `/ws?t=CÓDIGO`):** o celular envia `{"type":"press","id":"<botão>"}` e
`{"type":"save_layout","layout":{…}}`; o PC responde `result`, envia `layout` quando muda e um `tick`
por segundo com CPU/RAM/GPU, áudio e estado do clipe.

**Segurança:** só quem tem o código de acesso controla o PC. Botões "Rodar comando" executam qualquer
comando, então não compartilhe o código nem o QR code.
