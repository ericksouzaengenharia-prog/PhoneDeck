# Guia completo do PhoneDeck

O PhoneDeck tem duas partes:

* **Servidor no PC** (Python, Windows 10/11): recebe os toques e executa as ações.
* **App no iPhone** (app web): abre pelo Safari e vira um ícone na Tela de Início, em tela cheia.

---

## 1. Instalação no PC (uma vez só)

1. Dê dois cliques em **`iniciar.bat`**.
   * Se o Python não existir, ele pergunta se pode instalar o **Python 3.12** automaticamente: aperte **S**.
     Também dá para instalar manualmente em <https://www.python.org/downloads/> (marque **"Add python.exe to PATH"**).
   * Na primeira vez ele instala as bibliotecas (1–2 minutos).
2. Instale o **ffmpeg** (usado pelo clipe): `winget install --id Gyan.FFmpeg -e`
3. Para usar o **cabo**, instale o app **Dispositivos Apple** (Microsoft Store) ou o **iTunes**: eles trazem o driver da rede do iPhone pelo USB.
4. Se o **Firewall do Windows** perguntar, permita em redes **Privadas e Públicas**. A rede do cabo do iPhone costuma ser "Pública".

No fim, o `iniciar.bat`:

* cria o ícone **PhoneDeck** na área de trabalho;
* coloca o PhoneDeck na **inicialização do Windows**: ele fica esperando em segundo plano, sem janela, e ativa sozinho quando o cabo do iPhone é conectado, com um aviso no canto da tela;
* liga o PhoneDeck e abre a página de conexão com os QR codes.

> Rodou uma versão nova? Rode o `iniciar.bat` de novo: ele desliga a cópia antiga e liga a nova.
> Quando a organização dos botões muda, o PhoneDeck guarda uma cópia da anterior (`layout_vN_backup.json`) e mantém o que você personalizou.
> Se ainda houver uma **janela preta** da versão 1.0 aberta, feche-a antes.

### Os arquivos `.bat`

| Arquivo | Para quê |
|---|---|
| `iniciar.bat` | Instala/atualiza, cria os atalhos e liga em segundo plano |
| `modo_console.bat` | Liga numa janela visível, mostrando tudo o que acontece (bom para achar erros) |
| `remover_atalhos.bat` | Tira o ícone da área de trabalho e o início automático, e desliga o PhoneDeck |
| `criar_exe.bat` | Gera um `PhoneDeck.exe` único (opcional) |

**Desligar:** abra o ícone **PhoneDeck** da área de trabalho e clique em **Desligar o PhoneDeck**, no fim da página.

## 2. Conectar o iPhone

### Pelo cabo USB (recomendado)

1. No iPhone: **Ajustes › Ponto de Acesso Pessoal › Permitir Outros Conectarem** (ligado).
2. Conecte o cabo e toque em **Confiar**, se o iPhone perguntar.
3. Na página do PC aparece o cartão verde **"Cabo USB"** (endereço `172.20.10.x`). A página atualiza sozinha.
4. Aponte a câmera do iPhone para esse QR code e abra o link no Safari.

> O Ponto de Acesso precisa estar disponível no seu plano de celular. Se a opção estiver cinza, use o Wi-Fi.

**Para não gastar dados móveis:** com o cabo, o Windows pode mandar a internet do PC pelo iPhone. Para evitar, abra o
PowerShell **como administrador** e rode os comandos abaixo, trocando "Ethernet 3" pelo nome que aparecer no primeiro:
```powershell
Get-NetAdapter | Where-Object InterfaceDescription -like "*Apple*"
Set-NetIPInterface -InterfaceAlias "Ethernet 3" -InterfaceMetric 500
```

### Pelo Wi-Fi

Com o PC e o iPhone na mesma rede, escaneie o QR code do cartão "Rede: …".

### Instalar na Tela de Início

No Safari: **Compartilhar › Adicionar à Tela de Início**. Depois, abra sempre pelo ícone: ele abre em tela cheia e já guarda o código de acesso.

**Para a tela não apagar:** Ajustes › Tela e Brilho › Bloqueio Automático › **Nunca** (com o cabo, o iPhone fica carregando).

## 3. As páginas

Os botões vêm divididos em três páginas para ficarem **grandes** (3 colunas em pé, 5 deitado, sem rolar):

| Página | Botões |
|---|---|
| **Principal** | Painel do **Spotify** (capa, aleatório, anterior, play/pause, próxima) · **Microfone** · **Área de trabalho** · **Mudo** · **Vol −** · **Vol +** · **Fortnite** · **Rocket League** · **Battlefield 6** · **Mouse e teclado** |
| **PC** | **FPS do jogo** · Gráficos de **GPU**, **CPU**, **RAM** e **temperatura** · Print · Meus clipes · Gerenciador · **Bloquear PC** e **Fechar janela** (precisam segurar) |
| **Mais** | Anterior/Play/Próxima · Mutar Discord · Abrir Spotify · Navegador · VRAM · Volume · Digitar texto · Calculadora · Hora · Clipe 30s · Explorador |

Troque de página **deslizando a grade para o lado** (como na tela de início do iPhone) ou tocando nas abas (no topo, ou do lado
esquerdo com o celular deitado). No PC, use as setas ← → do teclado.

* **Clipe 15s** fica **fixo no topo**, embaixo das abas: aparece em todas as páginas (veja "Botões fixos").
* **Clipe:** a bolinha no canto mostra o estado (verde = gravando).
* **Gráficos:** mostram o último minuto, com **máx / méd / mín** ao lado do número. **Toque para abrir em tela cheia**; no PC, passe o mouse sobre o gráfico para ler cada segundo.
* **Microfone / Mudo:** ficam vermelhos quando estão mutados.

### Toque à prova de engano

* O botão **só aciona quando você solta o dedo** em cima dele. Encostou no botão errado? **Arraste o dedo para fora** antes de soltar e nada acontece.
* Botões com o **reloginho** no canto (Bloquear PC, Fechar janela) precisam ficar **apertados meio segundo**: uma faixa enche o botão e ele aciona.
* Enquanto um dedo aperta um botão, outros toques são ignorados (a palma da mão não aciona nada sem querer).
* Começou a deslizar para trocar de página em cima de um botão? Ele é cancelado: deslizar nunca aciona nada.
* Prefere a resposta instantânea? **Ajustes › Toque › Ao encostar**.
* Para exigir "segurar" em qualquer botão: modo edição › toque no botão › **Segurar para acionar**.

### Botões fixos

Um botão fixo aparece **em todas as páginas**: embaixo das abas Principal / PC / Mais (com o celular em pé), na coluna da
esquerda logo abaixo das abas (deitado) e no topo da **tela cheia**. Assim dá para salvar um clipe sem sair do gráfico de FPS.

* Vem com o **Clipe 15s** fixo.
* Para fixar outro botão: modo edição › toque no botão › **Fixar no topo**. Até 3 botões fixos.
* Para tirar: desmarque **Fixar no topo**; ele volta para a página que estiver aberta.
* Gráficos e o painel de música não podem ser fixos (são grandes demais para a faixa).

### Mouse e teclado

O botão **Mouse e teclado** (página Principal) transforma o celular num touchpad com teclado, para mexer no PC de longe.

| No touchpad | Faz |
|---|---|
| Arrastar 1 dedo | move o ponteiro (rápido = vai longe, devagar = preciso) |
| Tocar | clique |
| Tocar com 2 dedos | botão direito |
| Arrastar 2 dedos | rola a página (como no iPhone) |
| Tocar duas vezes e arrastar | arrasta (segura o clique) |

* **Esquerdo / Direito / meio:** botões de verdade. Segure um e arraste no touchpad com o outro dedo para selecionar ou arrastar.
* **vel. − / +**: velocidade do ponteiro (1 a 5). O Windows ainda aplica a velocidade do mouse dele.
* **Teclado** (ícone no canto): abre o teclado do iPhone; cada letra vai na hora para o PC (aceita acentos e emoji).
* Faixa de teclas: Esc, Tab, setas, apagar, Del, Enter, Print, F5, F11 e atalhos prontos (Alt+Tab, Copiar, Colar, Desfazer,
  Selecionar tudo, Área de trabalho). **Ctrl, Alt, Shift e Win** ficam acesos até a próxima tecla: Ctrl + c = copiar.
* Fecha no ✕. Se o celular desconectar no meio de um arrasto, o PC solta o botão sozinho.
* Quem tem o código de acesso consegue mexer no PC: não divulgue o código. Para desligar esta função, use
  `"remote_control": false` no `settings.json`.

### Tela cheia

Para acompanhar de longe, com tudo grande:

* **Toque num gráfico** (FPS, GPU, CPU, RAM, temperatura, VRAM) ou no **painel de música** (fora dos botões dele),
  ou no botão de **tela cheia** na barra de cima.
* Os **botões fixos** (ex.: Clipe 15s) aparecem no topo da tela cheia.
* **Deslize para os lados** para passar pelos itens. Os pontinhos embaixo mostram onde você está.
* **Música:** capa grande, música, artista, tempo, e os botões aleatório, anterior, play/pause e próxima.
* **Gráficos:** número grande, caixas de **máx / méd / mín** (e **1% low** no FPS), gráfico com escala e a linha da média.
  Escolha **1 min** ou **5 min** no canto de cima. **Toque no gráfico** para ler o valor daquele momento (no PC, passe o mouse).
* **Fechar:** botão ✕, arrastar para baixo, ou `Esc` no PC.
* A tela do iPhone **não apaga** enquanto a tela cheia está aberta (iOS 18.4 ou mais novo).
* No PC, a tela cheia ocupa o monitor inteiro e tem setas nas laterais.

**O que aparece e em que ordem:** modo edição › ajustes › **Tela cheia**. O padrão é Controles de música, GPU, CPU, RAM e FPS.
Marque ou desmarque os itens e use as setas para mudar a ordem. Os gráficos usam a cor do bloco deles na grade.

### Botões de jogos

Os botões **Fortnite**, **Rocket League** e **Battlefield 6** são do tipo **Jogo instalado**: o PhoneDeck procura o jogo
no seu PC e abre pelo launcher onde ele está instalado.

* **Epic Games:** lê os dados que a própria Epic guarda de cada jogo instalado e monta o mesmo link do "Criar atalho" da Epic.
* **EA app:** encontra a pasta do jogo e usa o link do EA app (`origin2://`). Se não achar, abre o `.exe` principal,
  que chama o EA app sozinho.
* **Steam:** lê as bibliotecas da Steam.
* **Atalhos do Windows:** atalhos da Área de Trabalho e do Menu Iniciar (Riot, Battle.net, Xbox, Discord…).

Para escolher o jogo exato: modo edição › toque no botão › **Lista** › escolha na lista (dá para buscar pelo nome).
A página do PC (ícone PhoneDeck) mostra em **Jogos encontrados no PC** tudo o que foi detectado.

**Se um jogo ainda não abrir:**
1. Veja se ele aparece em *Jogos encontrados no PC*. Se não aparecer, crie um atalho do jogo pelo launcher
   (Epic: **Biblioteca › … › Gerenciar › Criar atalho na área de trabalho**) e escolha esse atalho no botão
   (grupo **Atalhos do Windows**).
2. Se aparecer e mesmo assim der erro, anote a mensagem que surge no celular ou na tela do PC.

### FPS do jogo

O bloco **FPS** (página PC) mostra o FPS do jogo aberto, com gráfico do último minuto e **máx / méd / mín** ao lado.
Embaixo do nome aparece o jogo medido e o tempo de cada quadro (ex.: `Fortnite · 6,9 ms`).
**Toque no bloco** para abrir em tela cheia, onde aparece também o **1% low**: o FPS dos piores quadros, que é o que você sente como "engasgo".

* O 1% low pode ficar **abaixo do mín**: o mín é o pior segundo (média de 1 s), e o 1% low mede quadros soltos.
* Mede o **jogo em primeiro plano**. Ao trocar para o Discord ou o navegador, ele continua mostrando o último jogo.
* Funciona com qualquer jogo DirectX, Vulkan ou OpenGL, de qualquer launcher, sem sobreposição na tela e sem mexer no jogo
  (usa o **PresentMon**, ferramenta gratuita da Intel que lê os eventos do próprio Windows).
* A escala do gráfico acompanha o seu FPS (60, 90, 120, 150, 240…).
* Só mede enquanto o celular está conectado e o bloco FPS existe em alguma página.

**Primeira vez:** o `iniciar.bat` baixa o PresentMon para a pasta `ferramentas` e pergunta se pode **liberar a medição**.
Responda **S** e aceite o pedido de administrador (uma vez só). Depois **saia e entre de novo na sua conta do Windows**
(ou reinicie o PC). Isso coloca seu usuário no grupo *Usuários de log de desempenho*, que o Windows exige para ler
o FPS dos jogos. Quem já roda o PhoneDeck como administrador não precisa disso.

Também dá para fazer pela página do PC (ícone PhoneDeck): na linha **FPS** aparecem os botões **Baixar PresentMon**
e **Liberar FPS** quando falta alguma coisa.

**FPS na tela principal:** modo edição › **Adicionar** › ação **Mostrador ao vivo** › **FPS** › tamanho **2×1**
(no 1×1 ele mostra só o número e o gráfico).

## 4. Editar os botões

* Toque no **lápis** para entrar no modo edição (os botões balançam).
* Toque num botão para mudar **nome, ação, tamanho, ícone, cor** e **Segurar para acionar**, mover para os lados, duplicar ou excluir.
* **Adicionar** (último quadrado) cria um botão novo.
* **＋** na barra de abas cria uma página. Toque na aba atual para renomear, mover ou excluir a página.
* O ícone de **ajustes** (ao lado do ✓) tem os temas, o jeito de tocar (ao soltar / ao encostar), o número de colunas, os nomes nos botões e a vibração.
* Toque no **✓** para sair. Tudo é salvo no PC, no arquivo `layout.json`.

Também dá para editar pelo PC: abra o ícone PhoneDeck › **Abrir o deck aqui no PC**. No campo de atalho existe um botão de
teclado: clique nele e aperte o atalho para gravá-lo.

### Tamanhos

`1×1` normal · `2×1` largo · `1×2` alto · `2×2` grande · `3×1` faixa · `3×2` painel · `4×1` / `4×2` largos.
A grade encaixa os blocos sozinha e preenche os buracos.

### Tipos de ação

| Ação | Exemplo / observação |
|---|---|
| Mídia / volume | play/pause, próxima, anterior, parar, vol +, vol −, mudo |
| Painel de música | Spotify, ou "qualquer player" (o que estiver tocando: navegador, Deezer…) |
| Mutar microfone | alterna o microfone padrão do Windows |
| Atalho de teclado | `ctrl+shift+m`, `alt+f10`, `win+g`; sequência: `ctrl+c, alt+tab, ctrl+v` |
| Clipe da tela | segundos, até o tamanho do buffer (padrão 30 s) |
| Mostrar área de trabalho | Win+D |
| Abrir jogo instalado | escolha na lista (Epic, EA app, Steam ou atalhos do Windows) ou escreva o nome |
| Abrir programa, pasta ou site | `https://twitch.tv`, `spotify:`, `discord:`, `C:\Programas\app.exe`, `%USERPROFILE%\Downloads` |
| Rodar comando | `shutdown /s /t 60` (desliga em 1 min), qualquer comando do cmd |
| Digitar texto | digita no programa em foco (aceita acentos e emoji) |
| Mouse e teclado | abre o touchpad e o teclado no celular |
| Mostrador ao vivo | FPS do jogo, GPU, temperatura da GPU, VRAM, CPU, RAM, volume, relógio |
| Ir para outra página | navegação entre páginas |
| Abrir pasta de clipes / Bloquear o PC / Nada | — |

Teclas aceitas: `ctrl shift alt win`, `a–z`, `0–9`, `f1–f24`, `enter esc tab space backspace delete insert home end pageup pagedown up down left right printscreen pause capslock`, `num0–num9`, `add subtract multiply divide`, `playpause nexttrack prevtrack volumeup volumedown volumemute`.

## 5. Temas

**Ajustes › Tema**: Clássico, Minimal, Neon, Fofo, Liquid Glass e Gamer RGB.
**Aparência**: Automático (segue o claro/escuro do iPhone), Escuro ou Claro.
A cor que você escolhe para cada botão continua valendo: cada tema só muda o jeito de usá-la (fundo sólido, ícone colorido,
borda neon, tom pastel, vidro tingido…).

## 6. Clipe dos últimos segundos

Enquanto o celular está conectado (pelo cabo ou aberto no app), o PhoneDeck:

* grava a tela em pedaços de 2 s numa pasta temporária que se sobrescreve, sem encher o disco;
* grava o **som do PC** (o que sai no fone/caixa padrão) e o **microfone** numa "fita" na memória RAM.

Ao tocar no botão, ele junta os últimos N segundos de imagem e de som num `.mp4` em **Vídeos\PhoneDeck**.
Sem celular conectado por 10 minutos, a gravação entra em espera para não pesar no PC.

* Captura pela placa de vídeo (Desktop Duplication) e codifica nela quando possível (NVIDIA → AMD → Intel → CPU).
  A imagem vai **direto da captura para o codificador da placa**, sem passar pela memória do PC.
* A gravação roda com **prioridade alta** (CPU acima do normal, fora do modo economia do Windows e prioridade alta na fila da GPU),
  para não ficar sem vez quando o jogo usa a placa toda.
* Depois de salvar, o PhoneDeck **confere o clipe**: conta quantos quadros *novos* por segundo ele tem e avisa no celular
  ("Clipe conferido: 30 fps ✔"). O resultado também aparece na página do PC.
* Não precisa de "Mixagem estéreo": o som do PC é capturado direto do Windows (WASAPI).
* Trocou o fone ou o microfone padrão? Ele acompanha sozinho.

**Som fora de sincronia?** Ajuste `video_delay_ms` no `settings.json`: se o som vem **antes** da imagem, aumente (ex.: 250);
se vem **depois**, diminua (ex.: 50).

### Clipe travado ou picotado em jogo pesado

O arquivo sempre sai com 30 fps, mas quando a placa de vídeo está no limite (99% de uso), a captura não consegue pegar
imagens novas a tempo e repete a anterior. O vídeo fica "picotado". O aviso **"Clipe com só X fps"** no celular indica isso.

1. **Limite o FPS do jogo** uns 10% abaixo do que ele costuma alcançar (ou ao Hz do monitor). É o que mais resolve:
   a placa ganha folga para gravar e o jogo quase não muda. No Battlefield 6, Fortnite e Rocket League isso fica nas
   opções de vídeo/gráficos (limite de quadros / FPS máximo). Também dá para usar o limitador do painel da NVIDIA ou AMD.
2. Use o jogo em **tela cheia sem bordas** (janela sem bordas). A captura de tela fica mais estável.
3. Veja na página do PC a linha **Clipe**: o ideal é `direto na GPU` e `prioridade na GPU: alta`.
4. Ainda picotado? Use o replay do driver, que grava direto no chip de vídeo com perda mínima: **NVIDIA Instant Replay**
   (GeForce/NVIDIA App, atalho `alt+f10`) ou **AMD Instant Replay** (Adrenalin, atalho `ctrl+shift+s`), no modo atalho abaixo.

**Já usa NVIDIA Instant Replay, AMD Instant Replay, Xbox Game Bar ou o Replay Buffer do OBS?** Use o modo atalho:
```json
"clip": { "mode": "hotkey", "hotkey": "alt+f10" }
```
(`alt+f10` = NVIDIA; `ctrl+shift+s` = AMD; `win+alt+g` = Xbox Game Bar; no OBS, o atalho que você definiu para "Salvar replay".)

## 7. Arquivo `settings.json`

Criado na primeira execução, na pasta do PhoneDeck. **Desligue o PhoneDeck antes de editar.** Este arquivo contém o seu código de acesso: não publique.

| Campo | Padrão | Para que serve |
|---|---|---|
| `port` | 8765 | Porta do servidor |
| `token` | aleatório | Código de acesso do celular |
| `require_token` | true | Exige o código (deixe ligado) |
| `open_browser_on_start` | true | Abre a página de QR code ao ligar pelo ícone |
| `notify_on_cable` | true | Aviso do Windows quando o cabo do iPhone conecta |
| `buffer_always_on` | false | `true` = grava o clipe sempre, mesmo sem celular conectado |
| `remote_control` | true | `false` = desliga o Mouse e teclado (o celular não mexe no ponteiro nem digita) |
| `ffmpeg_path` | "" | Caminho do ffmpeg.exe, se não estiver no PATH |
| `clip.mode` | "ffmpeg" | `ffmpeg`, `hotkey` ou `off` |
| `clip.buffer_seconds` | 30 | Quantos segundos ficam guardados (máx. 300) |
| `clip.fps` | 30 | Quadros por segundo |
| `clip.capture` | "auto" | `auto`, `ddagrab` (GPU) ou `gdigrab` (compatível) |
| `clip.monitor` | 0 | Qual monitor gravar (0 = principal) |
| `clip.encoder` | "auto" | `auto`, `h264_nvenc`, `h264_amf`, `h264_qsv`, `libx264` |
| `clip.bitrate` | "8M" | Qualidade (use 12M–20M em 1440p/4K) |
| `clip.boost` | true | Prioridade alta para a gravação (CPU, GPU e sem modo economia). `false` = prioridade baixa, como antes |
| `clip.check_fps` | true | Confere cada clipe salvo e avisa quantos fps reais ele tem |
| `clip.draw_mouse` | true | Desenha o cursor no clipe |
| `clip.system_audio` | true | Grava o som do PC |
| `clip.microphone` | true | Grava o microfone |
| `clip.system_volume` / `clip.mic_volume` | 1.0 | Volume de cada um no clipe (0.0 a 2.0) |
| `clip.video_delay_ms` | 150 | Ajuste fino do sincronismo som/imagem |
| `clip.hotkey` | "alt+f10" | Atalho usado no modo `hotkey` |
| `clip.output_dir` | "" | Pasta dos clipes (vazio = Vídeos\PhoneDeck) |
| `fps.presentmon_path` | "" | Caminho do PresentMon.exe, se não estiver na pasta `ferramentas` |
| `fps_permission_asked` | false | `iniciar.bat` já perguntou se pode liberar a medição de FPS (volte para `false` para perguntar de novo) |

## 8. Problemas comuns

| Problema | Solução |
|---|---|
| "Python não encontrado" | O `iniciar.bat` oferece instalar. Ou instale pelo python.org marcando "Add python.exe to PATH". |
| Não aparece o cartão "Cabo USB" | Ligue o Ponto de Acesso **antes** de conectar o cabo; confira o app Dispositivos Apple/iTunes; troque de porta ou de cabo. |
| O iPhone fica em "Procurando o PC…" | Firewall: Painel de Controle › Firewall do Windows › Permitir um aplicativo › marque **Python** em Privada **e** Pública. |
| Pede código de acesso | Digite o código da página do PC (ícone PhoneDeck). |
| Atalhos não funcionam dentro de um jogo | Se o jogo roda como administrador, rode o PhoneDeck como administrador também. |
| Mouse e teclado não mexem numa janela | Mesma regra: janelas de administrador (Gerenciador de Tarefas, instaladores) só aceitam se o PhoneDeck também rodar como administrador. A tela de bloqueio e o UAC nunca aceitam. |
| Bolinha vermelha no botão de clipe | ffmpeg não instalado ou falhou. Veja `%TEMP%\phonedeck_buffer\ffmpeg_log.txt`; tente `"capture": "gdigrab"`. |
| Clipe picotado / "Clipe com só X fps" | Veja "Clipe travado ou picotado em jogo pesado" na seção 6: limite o FPS do jogo. |
| Clipe sem som | Veja na página do PC a linha "Áudio no clipe". Rode o `iniciar.bat` de novo para instalar as bibliotecas de áudio. |
| Painel do Spotify em "Spotify fechado" | Abra o Spotify **do PC** (o app). No modo "qualquer player", ele mostra o que estiver tocando. |
| Aleatório não funciona | O Spotify aceita; navegadores e alguns players não oferecem aleatório para o Windows. |
| FPS: "abra um jogo" com o jogo aberto | Clique no jogo para ele ficar em primeiro plano. Jogos em janela que não desenham nada parado também ficam sem dado. |
| FPS: "falta liberar no PC" | Página do PC › **Liberar FPS** › aceite o administrador › **saia e entre de novo** na conta do Windows. |
| FPS: "falta o PresentMon" | Página do PC › **Baixar PresentMon**, ou baixe `PresentMon-…-x64.exe` no GitHub da Intel (GameTechDev/PresentMon) e salve em `ferramentas\PresentMon.exe`. |
| GPU mostra "—" | NVIDIA mostra tudo. AMD/Intel mostram só o uso %, a partir do Windows 10 (1709). |
| Erro ao ligar / nada acontece | Rode `modo_console.bat` para ver a mensagem. O registro fica em `phonedeck.log`. |

## 9. Para desenvolvedores

* **Testar sem Windows:** `pip install -r requirements.txt` e `python servidor/main.py`. Fora do Windows, o servidor entra em
  **modo demonstração**: gráficos, música e áudio fictícios, e as ações só aparecem no console.
* **Criar uma ação nova:** (1) trate o `type` novo em `servidor/actions.py`; (2) inclua o nome em `ACTION_TYPES`
  no `config.py`; (3) adicione a opção em `ACTIONS` e os campos em `renderParams()` no `web/app.js`.
* **Criar um tema:** copie um bloco `body[data-theme="…"]` no fim de `web/style.css`, inclua o nome em `THEMES`
  (`config.py` e `web/app.js`).
* **Protocolo (WebSocket `/ws?t=CÓDIGO`):** o celular envia `{"type":"press","id":"<botão>","sub":"next"}` e
  `{"type":"save_layout","layout":{…}}`. O PC responde `result`, envia `layout` quando muda e um `tick` por segundo com
  CPU/RAM/GPU, áudio, clipe, música e cabo. A mensagem `hello` traz o layout e o histórico dos gráficos.
* **Rotas HTTP:** `/` (app), `/conectar` (só no próprio PC), `/ping`, `/status.json`, `/art/<spotify|any>` (capa), `POST /desligar`.
