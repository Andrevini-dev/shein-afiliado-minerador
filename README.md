# Minerador de links de afiliado SHEIN

Programinha que gera **links de afiliado da SHEIN** em quantidade, sozinho, no seu PC com Windows.
Você escolhe o que quer buscar (ex.: "vestido", "blazer", "bolsa") e quantos links quer. No fim sai um arquivo `.txt` com uma mensagem pronta por produto, no mesmo padrão do app (é só copiar e mandar no grupo):

```
Não perca esta oferta grande na SHEIN! Economize muito agora!
💰Preço[R$53,52] -20%
🛒SHEIN Franclia Vestido Curto Feminino Novo em Tecido de Malha de Cetim...
🎁Cupom 50% OFF para todo Novo Usuário!
https://onelink.shein.com/60/...._KOC-C

Não perca esta oferta grande na SHEIN! Economize muito agora!
...
```

Prefere só uma lista numerada (`01 • título` + link)? Troque `formato_saida` para `"lista"` no `config.json`.

> **Por que precisa de um "Android"?** O Programa de Afiliados da SHEIN só funciona no **aplicativo** (o site avisa "acessível apenas em dispositivos móveis"). O programa "toca" no app por você e lê o link que aparece na tela. Isso só é possível com Android:
>
> | Seu celular | Como usar |
> |---|---|
> | **iPhone** (ex.: iPhone 14 Plus) | A Apple não deixa o PC controlar o iPhone. Use o **BlueStacks**: um "celular Android" de mentira que roda dentro do PC. Você entra na sua conta SHEIN nele uma vez e pronto. → **Caminho A** |
> | **Android** (Samsung, Xiaomi, Motorola...) | Pode usar o próprio celular no cabo USB. → **Caminho B** (ou o Caminho A, se preferir) |

---

## ⚠️ Antes de usar

- **Uso pessoal.** Feito para uma afiliada gerar os próprios links.
- **Ritmo baixo de propósito:** pausas aleatórias de 3 a 8 segundos entre produtos e um descanso de 1 a 2 minutos a cada 25 links. Não diminua isso.
- **Respeite os termos do Programa de Afiliados SHEIN.** Se aparecer verificação de robô, o programa **para e espera você resolver**; ele nunca tenta burlar.
- O programa **não pede, não guarda e não digita senha nenhuma.** O login na SHEIN é sempre você quem faz.
- **Segurança:** antes de cada toque ele confere se a SHEIN está na frente da tela. Se entrar uma ligação ou abrir outro app, ele não toca em nada e espera.

---

## Passo a passo (só na primeira vez)

### 1. Instalar o Python
1. Entre em <https://www.python.org/downloads/> e clique no botão amarelo **Download Python**.
2. Abra o instalador e **marque a caixinha "Add python.exe to PATH"** (lá embaixo) antes de clicar em **Install Now**.

### 2. Baixar o "adb" (programa do Google que conversa com o Android)
1. Baixe: <https://dl.google.com/android/repository/platform-tools-latest-windows.zip>
2. Clique com o botão direito no arquivo baixado → **Extrair tudo...** → extraia para `C:\` .
   Vai ficar uma pasta `C:\platform-tools` com o `adb.exe` dentro.

### 3A. Caminho A: iPhone (ou quem não quer usar o celular) → BlueStacks no PC
1. Baixe e instale o BlueStacks pelo site oficial: <https://www.bluestacks.com> (botão **Baixar BlueStacks**).
2. Abra o BlueStacks e clique na **engrenagem (Configurações)**:
   - **Tela / Display** → em **Orientação** escolha **Retrato (Portrait)** e resolução **1080 x 1920**. (O programa foi feito para tela em pé, como um celular.)
   - **Avançado / Advanced** → ligue **Android Debug Bridge (ADB)**. Embaixo aparece um endereço como `127.0.0.1:5555`; anote.
   - Clique em **Salvar** e reinicie o BlueStacks se ele pedir.
3. Dentro do BlueStacks abra a **Play Store**, entre com uma conta Google (pode ser a sua de sempre) e instale o app **SHEIN**.
4. Abra a SHEIN no BlueStacks e **entre na sua conta de afiliada** (o mesmo login do seu iPhone).
5. Confira: **Perfil → Affiliate & Creator** tem que abrir a sua Central de Afiliados (com o saldo e "Pesquisar produtos").
6. No passo 5 (configuração), preencha `"emulador": "127.0.0.1:5555"` (o endereço que você anotou).

> Usa outro emulador (MuMu, LDPlayer, Nox, MEmu)? Também funciona: ligue o ADB/"depuração" nele e coloque o endereço em `"emulador"`. Se deixar vazio, o programa tenta achar sozinho os mais comuns.

### 3B. Caminho B: celular Android no cabo USB
1. No celular: **Configurações → Sobre o telefone** → toque **7 vezes** em **Número da versão** (no Xiaomi é **Versão do MIUI / HyperOS**) até aparecer "Você agora é um desenvolvedor".
2. Volte e entre em **Configurações adicionais → Opções do desenvolvedor** e ligue:
   - **Depuração USB**
   - (só Xiaomi) **Depuração USB (configurações de segurança)**; sem isso o PC não consegue tocar na tela.
3. Ligue o celular no PC com o cabo USB. Vai aparecer "Permitir depuração USB?" → marque **Sempre permitir** → **OK**.
4. Abra o app da **SHEIN** e confira que está logada na **conta de afiliada**.

### 4. Baixar este programa
- Jeito fácil: aqui no GitHub clique no botão verde **Code → Download ZIP** e extraia (ex.: em `Documentos\shein-afiliado-minerador`).
- Ou, se tiver o Git instalado, abra o Prompt de Comando e rode:

```bat
git clone https://github.com/Andrevini-dev/shein-afiliado-minerador.git
```

Não precisa instalar nenhum pacote extra (o `requirements.txt` está vazio de propósito).

### 5. Ajustar a configuração
1. Dentro da pasta do programa, copie o arquivo `config.exemplo.json` e renomeie a cópia para **`config.json`**.
2. Abra o `config.json` no Bloco de Notas e ajuste:

| Campo | O que é | Exemplo |
|---|---|---|
| `buscas` | o que pesquisar (um termo por item) | `["vestido", "blazer", "bolsa"]` |
| `quantidade_alvo` | quantos links no total | `100` |
| `koc_id_afiliada` | seu ID de afiliada. **Deixe vazio na 1ª vez**: o programa descobre e mostra | `""` |
| `adb` | onde está o adb | `"C:\\platform-tools\\adb.exe"` (com **duas** barras) |
| `emulador` | **só no Caminho A**: endereço do ADB do BlueStacks | `"127.0.0.1:5555"` |
| `celular_serial` | deixe vazio (só serve se tiver mais de um aparelho ligado) | `""` |
| `pausa_min_s` / `pausa_max_s` | pausa entre produtos, em segundos | `3` / `8` |
| `formato_saida` | `"mensagem"` (texto completo do app) ou `"lista"` (número + título + link) | `"mensagem"` |

---

## Rodar

1. **Caminho A:** BlueStacks aberto, com a SHEIN logada. **Caminho B:** celular no USB, desbloqueado, tela ligada.
2. Dê **dois cliques em `rodar.bat`** (ou, no Prompt de Comando dentro da pasta: `python minerador.py`).
3. O programa abre a **Central de Afiliados** sozinho (Perfil → Affiliate & Creator; se não der, pesquisa "afiliado"), busca cada termo e vai gerando os links. Na tela do PC aparece cada link gerado.
4. **Primeira vez:** ele mostra `ID da afiliada detectado no 1º link: koc_id=...`. Copie esse número para o campo `koc_id_afiliada` do `config.json`. A partir daí, se algum link sair com outro ID (outra conta logada), **o programa para na hora**.

Dicas:
- Não mexa no BlueStacks/celular enquanto roda. No celular, deixe a tela sem bloquear durante o uso (Configurações → Tela → Bloqueio automático → Nunca).
- Para parar: feche a janela ou aperte `Ctrl + C`. **Pode rodar de novo depois: ele continua de onde parou** e não repete produtos.
- Se aparecer CAPTCHA ou pedir login, o PC apita. Resolva na tela do BlueStacks/celular; o programa confere a cada 30 segundos e continua sozinho.

## Onde ficam os links

Na pasta **`saida`**, dentro da pasta do programa:

- `links_shein_AAAA-MM-DD.txt` → todas as mensagens do dia, uma linha em branco entre elas.
- `links_vestido.txt`, `links_blazer.txt`... → um arquivo por busca.
- `progresso.json` → controle interno (não apague se quiser continuar depois; apague para começar uma lista nova do zero).

Para refazer os `.txt` sem minerar de novo: `python minerador.py txt`.

---

## Problemas comuns

| Mensagem | O que fazer |
|---|---|
| `Não achei o adb` | Confira o passo 2 e o campo `adb` no `config.json`. |
| `Nenhum aparelho pronto` | **BlueStacks:** abra ele e confira se o ADB está ligado e o endereço em `emulador`. **Celular:** cabo USB que transfira dados, Depuração USB ligada, aceite o aviso. |
| `AVISO: a tela está deitada` | No BlueStacks, mude a orientação para **Retrato** (passo 3A). |
| `Esta conta da SHEIN NÃO é de afiliada` | A conta logada no app não é a de afiliada. Saia e entre na conta certa. |
| `Não consegui abrir a Central de Afiliados` | Abra você mesma no app (Perfil → Affiliate & Creator) e rode de novo. |
| `outro app está na frente` | Feche o que abriu (ligação, notificação) e volte para a SHEIN; ele continua sozinho. |
| Toques não acontecem (Xiaomi) | Ligue "Depuração USB (configurações de segurança)". |
| `PAREI: o link saiu com outro ID de afiliada` | O app está logado em outra conta. Entre na conta de afiliada. |

## Como funciona (para curiosas)

- `adb shell uiautomator dump` lê os textos da tela do app; `adb shell input tap` toca nos botões **Ganhe**. As posições são calculadas pelo tamanho da tela, então funciona em qualquer celular ou emulador em pé.
- O link aparece no texto de compartilhamento ("Compartilhe para ganhar"); o programa lê dali o texto inteiro, sem usar a área de transferência, e fecha o painel pelo **X** (o botão voltar sairia da busca).
- Cada link é aberto uma vez (só a página, sem navegador) para conferir o `koc_id` (sua afiliação) e o `goods_id` (o produto, usado para não repetir).
- Tudo é salvo depois de cada link em `saida/progresso.json`.
