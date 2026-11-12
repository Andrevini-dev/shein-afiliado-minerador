# Minerador de links de afiliado SHEIN

Programinha que gera **links de afiliado da SHEIN** em quantidade, sozinho, usando o seu celular Android ligado no PC.
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

> **Por que pelo celular?** O Programa de Afiliados da SHEIN só funciona no aplicativo (o site avisa "acessível apenas em dispositivos móveis"). Então o programa "toca" no app por você, pelo cabo USB, e lê o link que aparece na tela.

---

## ⚠️ Antes de usar

- **Uso pessoal.** Feito para uma afiliada gerar os próprios links.
- **Ritmo baixo de propósito:** pausas aleatórias de 3 a 8 segundos entre produtos e um descanso de 1 a 2 minutos a cada 25 links. Não diminua isso.
- **Respeite os termos do Programa de Afiliados SHEIN.** Se aparecer verificação de robô, o programa **para e espera você resolver** — ele nunca tenta burlar.
- O programa **não pede, não guarda e não digita senha nenhuma.**

---

## Passo a passo (só na primeira vez)

### 1. Instalar o Python
1. Entre em <https://www.python.org/downloads/> e clique no botão amarelo **Download Python**.
2. Abra o instalador e **marque a caixinha "Add python.exe to PATH"** (lá embaixo) antes de clicar em **Install Now**.

### 2. Baixar o "adb" (programa do Google que conversa com o celular)
1. Baixe: <https://dl.google.com/android/repository/platform-tools-latest-windows.zip>
2. Clique com o botão direito no arquivo baixado → **Extrair tudo...** → extraia para `C:\` .
   Vai ficar uma pasta `C:\platform-tools` com o `adb.exe` dentro.

### 3. Preparar o celular
1. No celular: **Configurações → Sobre o telefone** → toque **7 vezes** em **Número da versão** (no Xiaomi é **Versão do MIUI / HyperOS**) até aparecer "Você agora é um desenvolvedor".
2. Volte e entre em **Configurações adicionais → Opções do desenvolvedor** e ligue:
   - **Depuração USB**
   - (só Xiaomi) **Depuração USB (configurações de segurança)** — sem isso o PC não consegue tocar na tela.
3. Ligue o celular no PC com o cabo USB. Vai aparecer "Permitir depuração USB?" → marque **Sempre permitir** → **OK**.
4. Abra o app da **SHEIN** e confira que está logada na **conta de afiliada**.

### 4. Baixar este programa
- Jeito fácil: aqui no GitHub clique no botão verde **Code → Download ZIP**, e extraia (ex.: em `Documentos\shein-afiliado-minerador`).
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
| `pausa_min_s` / `pausa_max_s` | pausa entre produtos, em segundos | `3` / `8` |
| `formato_saida` | `"mensagem"` (texto completo do app) ou `"lista"` (número + título + link) | `"mensagem"` |

---

## Rodar

1. Celular ligado no USB, desbloqueado, tela ligada, com o app da SHEIN aberto.
2. Dê **dois cliques em `rodar.bat`** (ou, no Prompt de Comando dentro da pasta: `python minerador.py`).
3. O programa abre a **Central de Afiliados** sozinho (pesquisa "afiliado" no app), busca cada termo e vai gerando os links. Na tela do PC aparece cada link gerado.
4. **Primeira vez:** ele mostra `ID da afiliada detectado no 1º link: koc_id=...`. Copie esse número para o campo `koc_id_afiliada` do `config.json`. A partir daí, se algum link sair com outro ID (outra conta logada), **o programa para na hora**.

Dicas:
- Não mexa no celular enquanto roda (deixe a tela sem bloquear: Configurações → Tela → Bloqueio automático → Nunca, durante o uso).
- Para parar: feche a janela ou aperte `Ctrl + C`. **Pode rodar de novo depois: ele continua de onde parou** e não repete produtos.
- Se aparecer CAPTCHA ou pedir login no celular, o PC apita. Resolva no celular; o programa confere a cada 30 segundos e continua sozinho.

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
| `Nenhum celular pronto` | Cabo USB (use um que transfira dados), Depuração USB ligada, aceite o aviso no celular. |
| `Não consegui abrir a Central de Afiliados` | Abra você mesma no app (pesquise "Afiliado") e rode de novo. |
| Toques não acontecem (Xiaomi) | Ligue "Depuração USB (configurações de segurança)". |
| `PAREI: o link saiu com outro ID de afiliada` | O app está logado em outra conta. Entre na conta de afiliada. |

## Como funciona (para curiosas)

- `adb shell uiautomator dump` lê os textos da tela do app; `adb shell input tap` toca nos botões **Ganhe**.
- O link aparece no texto de compartilhamento ("Compartilhe para ganhar"); o programa lê dali o texto inteiro, sem usar a área de transferência, e fecha o painel pelo **X** (o botão voltar sairia da busca).
- Cada link é aberto uma vez (só a página, sem navegador) para conferir o `koc_id` (sua afiliação) e o `goods_id` (o produto, usado para não repetir).
- Tudo é salvo depois de cada link em `saida/progresso.json`.
