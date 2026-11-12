# -*- coding: utf-8 -*-
"""
Minerador de links de afiliado SHEIN.
Funciona com celular Android no USB ou com um emulador Android no PC
(BlueStacks etc.) — é o caminho para quem tem iPhone.

Como funciona, em poucas palavras:
  1. Um Android conectado pelo adb: celular no USB (Depuração USB ligada)
     ou emulador no PC com o ADB ligado.
  2. O app da SHEIN precisa estar logado na conta de AFILIADA.
  3. O programa abre a Central de Afiliados, pesquisa cada termo da lista
     (ex.: "vestido"), toca em "Ganhe" em cada produto e lê o link de
     afiliado que aparece escrito na tela.
  4. Cada link é conferido: ele precisa ter o mesmo ID de afiliada (koc_id).
  5. Tudo é salvo aos poucos em saida/progresso.json. Se cair, é só rodar de
     novo que ele continua de onde parou.
  6. No fim (ou a cada lote) ele gera os arquivos .txt na pasta "saida".

Só usa Python puro + o programa "adb" (Android Platform Tools).
Não instala nada no celular e não mexe em senha nenhuma.
"""

import json
import os
import random
import re
import subprocess
import sys
import time
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

# Deixa o terminal do Windows mostrar acentos e emojis sem erro
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PASTA = os.path.dirname(os.path.abspath(__file__))
PASTA_SAIDA = os.path.join(PASTA, "saida")
ARQ_PROGRESSO = os.path.join(PASTA_SAIDA, "progresso.json")
PACOTE_SHEIN = "com.zzkko"  # nome interno do app da SHEIN

# ----------------------------------------------------------------------------
# Configuração
# ----------------------------------------------------------------------------

def carregar_config():
    """Lê o config.json (ou o config.exemplo.json, se o primeiro não existir)."""
    for nome in ("config.json", "config.exemplo.json"):
        caminho = os.path.join(PASTA, nome)
        if os.path.exists(caminho):
            with open(caminho, encoding="utf-8") as f:
                cfg = json.load(f)
            print(f"Usando configuração: {nome}")
            return cfg
    sys.exit("Não achei config.json nem config.exemplo.json.")


CFG = carregar_config()
ADB = CFG.get("adb") or "adb"
SERIAL = CFG.get("celular_serial") or ""


# ----------------------------------------------------------------------------
# Conversa com o celular (adb)
# ----------------------------------------------------------------------------

def adb(*args, timeout=40):
    """Roda um comando adb e devolve o texto da saída ("" se demorar demais)."""
    cmd = [ADB] + (["-s", SERIAL] if SERIAL else []) + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return ""
    return r.stdout.decode("utf-8", errors="replace")


# Portas de ADB dos emuladores mais comuns no Windows (usado no iPhone: ver README)
PORTAS_EMULADOR = ["127.0.0.1:5555", "127.0.0.1:5556", "127.0.0.1:5565", "127.0.0.1:5575",  # BlueStacks
                   "127.0.0.1:7555", "127.0.0.1:16384",  # MuMu
                   "127.0.0.1:62001", "127.0.0.1:21503", "emulator-5554"]  # Nox, MEmu, LDPlayer/AVD

LARG, ALT = 1080, 2400  # tamanho da tela; é lido do aparelho em checar_celular()


def aparelhos_prontos():
    saida = subprocess.run([ADB, "devices"], capture_output=True, text=True, timeout=30).stdout
    linhas = [l for l in saida.splitlines()[1:] if l.strip()]
    return [l.split()[0] for l in linhas if l.split()[-1] == "device"], saida


def checar_celular():
    """Acha o aparelho: celular Android no USB ou emulador no PC (BlueStacks, MuMu...)."""
    global SERIAL, LARG, ALT
    try:
        prontos, saida = aparelhos_prontos()
    except FileNotFoundError:
        sys.exit("Não achei o adb. Veja o README (Platform Tools) e o campo \"adb\" do config.")
    emulador = (CFG.get("emulador") or "").strip()
    if emulador and emulador not in prontos:
        print(f"Conectando no emulador {emulador}...")
        subprocess.run([ADB, "connect", emulador], capture_output=True, timeout=30)
        prontos, saida = aparelhos_prontos()
        SERIAL = SERIAL or (emulador if emulador in prontos else "")
    if not prontos:
        # tenta achar sozinho um emulador aberto
        for end in PORTAS_EMULADOR:
            if end.startswith("127."):
                subprocess.run([ADB, "connect", end], capture_output=True, timeout=10)
        prontos, saida = aparelhos_prontos()
    if not prontos:
        sys.exit("Nenhum aparelho pronto.\n- Celular Android: ligue o cabo USB, ative a Depuração USB e aceite o aviso.\n"
                 "- Emulador (quem tem iPhone): abra o BlueStacks e ligue o ADB nas configurações (veja o README).\n" + saida)
    if not SERIAL:
        SERIAL = prontos[0]
    if SERIAL not in prontos:
        sys.exit(f"O aparelho {SERIAL} do config não está conectado. Conectados: {prontos}")
    tam = re.findall(r"(\d+)x(\d+)", adb("shell", "wm", "size"))
    if tam:
        LARG, ALT = (int(v) for v in tam[-1])  # usa o "Override size" se houver
    print(f"Aparelho conectado: {SERIAL} (tela {LARG}x{ALT})")
    if LARG > ALT:
        print("AVISO: a tela está deitada (paisagem). No emulador, use o modo retrato/celular (veja o README).")


def px(fracao_x=None, fracao_y=None):
    """Converte posição em fração da tela para pixels (funciona em qualquer tamanho)."""
    if fracao_y is None:
        return int(fracao_x * LARG)
    if fracao_x is None:
        return int(fracao_y * ALT)
    return int(fracao_x * LARG), int(fracao_y * ALT)


def pausa(minimo=None, maximo=None):
    """Espera um tempo aleatório, para o ritmo parecer de gente."""
    minimo = CFG.get("pausa_min_s", 3) if minimo is None else minimo
    maximo = CFG.get("pausa_max_s", 8) if maximo is None else maximo
    time.sleep(random.uniform(minimo, maximo))


def foco_atual():
    return adb("shell", "dumpsys", "window").split("mCurrentFocus", 1)[-1][:300]


def garantir_shein_na_frente():
    """SEGURANÇA: nunca toca em outro app. Se uma ligação, notificação ou outro app
    estiver na frente, espera e depois traz a SHEIN de volta."""
    avisou = False
    for tentativa in range(40):  # até ~10 minutos
        foco = foco_atual()
        if PACOTE_SHEIN in foco:
            return
        if not avisou:
            print(f"   outro app está na frente ({foco.strip()[:80]}); não vou tocar em nada, esperando...")
            avisou = True
        time.sleep(15)
        if tentativa >= 1:
            adb("shell", "monkey", "-p", PACOTE_SHEIN, "-c", "android.intent.category.LAUNCHER", "1")
            time.sleep(4)
    sys.exit("A SHEIN não voltou para a frente da tela. Abra o app e rode de novo.")


def tocar(x, y):
    garantir_shein_na_frente()
    # um pequeno desvio aleatório no ponto do toque
    adb("shell", "input", "tap", str(int(x + random.randint(-6, 6))), str(int(y + random.randint(-4, 4))))


def tecla(codigo):
    garantir_shein_na_frente()
    adb("shell", "input", "keyevent", str(codigo))


def rolar_para_baixo():
    garantir_shein_na_frente()
    y1 = px(fracao_y=random.uniform(0.69, 0.75))
    y2 = px(fracao_y=random.uniform(0.31, 0.375))
    x = px(fracao_x=random.uniform(0.44, 0.56))
    adb("shell", "input", "swipe", str(x), str(y1), str(x), str(y2), str(random.randint(500, 800)))


def sem_acento(txt):
    """O 'adb input text' não aceita acentos: 'calça' vira 'calca'."""
    return "".join(c for c in unicodedata.normalize("NFD", txt) if unicodedata.category(c) != "Mn")


def digitar(txt):
    garantir_shein_na_frente()
    txt = sem_acento(txt).replace(" ", "%s")
    adb("shell", "input", "text", txt)


def tela_atual():
    """Lê tudo o que está na tela do celular (textos, botões e posições)."""
    xml, inicio = "", -1
    for tentativa in range(3):
        # apaga a leitura anterior: se a nova falhar, não usamos uma tela velha
        adb("shell", "rm", "-f", "/sdcard/shein_ui.xml")
        saida = adb("shell", "uiautomator", "dump", "/sdcard/shein_ui.xml", timeout=20)
        if "dumped to" in saida:
            xml = adb("shell", "cat", "/sdcard/shein_ui.xml")
            inicio = xml.find("<?xml")
            if inicio >= 0:
                break
        time.sleep(1.5)  # emuladores às vezes precisam de uma segunda tentativa
    if inicio < 0:
        return []
    try:
        raiz = ET.fromstring(xml[inicio:].strip())
    except ET.ParseError:
        return []
    nos = []
    for n in raiz.iter("node"):
        b = [int(v) for v in re.findall(r"-?\d+", n.get("bounds", "[0,0][0,0]"))]
        nos.append({
            "texto": n.get("text", ""),
            "desc": n.get("content-desc", ""),
            "id": n.get("resource-id", "").split("/")[-1],
            "classe": n.get("class", "").split(".")[-1],
            "x1": b[0], "y1": b[1], "x2": b[2], "y2": b[3],
        })
    return nos


def centro(no):
    return (no["x1"] + no["x2"]) // 2, (no["y1"] + no["y2"]) // 2


def achar(nos, texto=None, contem=None, desc=None):
    for n in nos:
        if texto is not None and n["texto"].strip() == texto:
            return n
        if contem is not None and contem.lower() in n["texto"].lower():
            return n
        if desc is not None and n["desc"].strip() == desc:
            return n
    return None


def visivel(n):
    return n["y2"] > n["y1"] and n["x2"] > n["x1"]


# ----------------------------------------------------------------------------
# CAPTCHA e login: nunca burlar, só esperar a pessoa resolver
# ----------------------------------------------------------------------------

PALAVRAS_CAPTCHA = ("captcha", "verificação de segurança", "verifique que você", "não sou um robô",
                    "deslize para", "arraste o controle", "slide to", "verify you")
PALAVRAS_LOGIN = ("entrar / registrar", "entrar/registrar", "faça login", "fazer login", "iniciar sessão",
                  "entrar mais tarde", "insira o e-mail ou número de telefone", "prosseguir com google")


def bloqueio(nos):
    tudo = " ".join((n["texto"] + " " + n["desc"]).lower() for n in nos)
    if any(p in tudo for p in PALAVRAS_CAPTCHA):
        return "captcha"
    if any(p in tudo for p in PALAVRAS_LOGIN) and "programa de afiliados" not in tudo:
        return "login"
    return None


def esperar_pessoa(motivo):
    """Avisa e fica conferindo a cada 30 s até a tela ficar livre."""
    msg = {
        "captcha": "Apareceu uma verificação de robô (CAPTCHA) no celular. Resolva na tela do celular.",
        "login": "O app pediu login. Entre na conta de AFILIADA no celular.",
    }[motivo]
    print("\n" + "!" * 70 + f"\n{msg}\nVou conferir a cada 30 segundos e continuo sozinho.\n" + "!" * 70)
    if os.name == "nt":
        try:
            import winsound
            winsound.Beep(880, 400)
        except Exception:
            pass
    while True:
        time.sleep(30)
        if not bloqueio(tela_atual()):
            print("Liberado, continuando.")
            return


# ----------------------------------------------------------------------------
# Navegação no app
# ----------------------------------------------------------------------------

def na_central(nos):
    return achar(nos, texto="Programa de Afiliados") is not None


def esperar_central(segundos):
    """Espera a Central de Afiliados carregar (confere a cada 3 s)."""
    fim = time.time() + segundos
    while time.time() < fim:
        time.sleep(3)
        if na_central(tela_atual()):
            return True
    return False


def conta_nao_afiliada(nos):
    """A conta logada não é de afiliada: a SHEIN mostra a página de inscrição
    ("Afiliado Novo" no topo, com Registre-se/Entrar), e não a Central."""
    if na_central(nos):
        return False
    topo = " ".join(n["texto"].lower() for n in nos if n["y2"] < px(fracao_y=0.12))
    tudo = " ".join(n["texto"].lower() for n in nos)
    return ("torne-se um afiliado" in tudo
            or ("afiliado novo" in topo and "pesquisar produtos" not in tudo))


def ir_para_tela_inicial():
    """Abre o app (sem tocar em nada) e volta até as abas principais."""
    adb("shell", "monkey", "-p", PACOTE_SHEIN, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(4)
    for _ in range(6):
        if "MainTabsActivity" in foco_atual():
            break
        tecla(4)  # voltar
        time.sleep(1.5)
    nos = tela_atual()
    # 1ª abertura do app: tela de boas-vindas (país/moeda) → "Compre agora"
    boas_vindas = achar(nos, texto="Compre agora")
    if boas_vindas:
        tocar(*centro(boas_vindas))
        time.sleep(5)
        nos = tela_atual()
    return nos


def aba(nos, nome):
    """Botão de uma aba da barra de baixo (Loja, Categoria, ..., Perfil)."""
    return next((n for n in nos if n["texto"] == nome and n["y1"] > px(fracao_y=0.85)), None)


def abrir_central():
    """Abre a Central de Afiliados.
    Caminho 1: aba Perfil → "Affiliate & Creator" (posição fixa, funciona no celular e no emulador).
    Caminho 2: pesquisar "afiliado" na busca do app (caminho oficial da SHEIN)."""
    for tentativa in range(3):
        nos = tela_atual()
        if na_central(nos):
            return nos
        if conta_nao_afiliada(nos):
            sys.exit("Esta conta da SHEIN NÃO é de afiliada (apareceu 'Torne-se um afiliado').\n"
                     "Saia dela no app e entre na conta de afiliada, depois rode de novo.")
        motivo = bloqueio(nos)
        if motivo:
            esperar_pessoa(motivo)
            continue
        # se está numa página da própria Central (ex.: resultado de busca), voltar 1 tela basta
        if "WebViewActivity" in foco_atual():
            tecla(4)
            if esperar_central(8):
                return tela_atual()
        nos = ir_para_tela_inicial()
        motivo = bloqueio(nos)
        if motivo:
            esperar_pessoa(motivo)
            continue

        # Caminho 1: Perfil → Affiliate & Creator
        perfil = aba(nos, "Perfil")
        if perfil:
            tocar(*centro(perfil))
            time.sleep(4)
            nos = tela_atual()
            entrada = next((n for n in nos if re.search(r"affiliate|afiliad", n["texto"] + n["desc"], re.I)
                            and visivel(n)), None)
            if entrada:
                tocar(*centro(entrada))
                if esperar_central(30):
                    return tela_atual()
                if conta_nao_afiliada(tela_atual()):
                    continue  # o começo do laço avisa e para
                nos = ir_para_tela_inicial()

        # Caminho 2: busca "afiliado" na aba Loja
        loja = aba(nos, "Loja")
        if loja:
            tocar(*centro(loja))
            time.sleep(4)
            nos = tela_atual()
        lupa = achar(nos, desc="Pesquisa")
        barra = next((n for n in nos if n["classe"] == "EditText" and n["y2"] < px(fracao_y=0.15)), None)
        if lupa:
            tocar(px(0.45), centro(lupa)[1])  # meio da barra de busca (mesma altura da lupa)
        elif barra:
            tocar(*centro(barra))
        else:
            print("Não achei a barra de busca; tentando de novo...")
            continue
        time.sleep(2.5)
        if not any(n["classe"] == "EditText" for n in tela_atual()):
            print("O toque não abriu a busca; tentando de novo...")
            continue
        digitar("afiliado")
        time.sleep(1)
        tecla(66)  # Enter
        if esperar_central(30):
            return tela_atual()
    nos = tela_atual()
    if conta_nao_afiliada(nos):
        sys.exit("Esta conta da SHEIN NÃO é de afiliada. Entre na conta de afiliada e rode de novo.")
    if not na_central(nos):
        sys.exit("Não consegui abrir a Central de Afiliados. Abra no app (Perfil → Affiliate & Creator) "
                 "e rode de novo.")
    return nos


def pesquisar(termo):
    """Na Central de Afiliados, pesquisa um termo e espera a lista de produtos."""
    nos = abrir_central()
    campo = achar(nos, texto="Pesquisar produtos")
    tocar(*centro(campo))
    time.sleep(3)
    nos = tela_atual()
    caixa = next((n for n in nos if n["classe"] == "EditText"), None)
    if caixa:
        tocar(*centro(caixa))
        time.sleep(1)
        tecla(123)  # vai para o fim do texto
        for _ in range(40):
            tecla(67)  # apaga o que tinha
    time.sleep(1)
    digitar(termo)
    time.sleep(1)
    tecla(66)
    time.sleep(7)


def voltar_para_busca(termo):
    """Se um toque abriu outra tela (ex.: página do produto), volta para os resultados."""
    for _ in range(3):
        if "WebViewActivity" in foco_atual():
            break
        tecla(4)
        time.sleep(2)
    nos = tela_atual()
    if achar(nos, texto="Pesquisa") and cards_na_tela(nos):
        return
    if not achar(nos, contem="Compartilhe para ganhar"):
        print("   voltando para a busca...")
        pesquisar(termo)


def cards_na_tela(nos):
    """Acha os produtos visíveis: título, preço e o botão 'Ganhe' de cada um."""
    cards = []
    titulo = None
    precos = []
    for n in nos:
        t = n["texto"].strip()
        if not visivel(n):
            continue
        # título: bloco largo que começa na coluna do texto do produto
        if (px(0.33) <= n["x1"] <= px(0.45) and n["x2"] > px(0.83) and len(t) > 15
                and "vendido" not in t.lower() and not t.startswith("R$")):
            titulo, precos = t, []
        elif titulo and re.fullmatch(r"R\$[\d.]+,\d{2}", t):
            precos.append(t)
        elif titulo and t == "Ganhe" and n["classe"] == "Button":
            # só usa botões inteiros na tela (longe do topo e da barra de baixo)
            if n["y1"] > px(fracao_y=0.125) and n["y2"] < px(fracao_y=0.83):
                cards.append({"titulo": titulo, "preco": precos[0] if precos else "", "botao": n})
            titulo, precos = None, []
    return cards


def ler_painel(nos):
    """Lê o texto de compartilhamento que aparece depois de tocar em 'Ganhe'.
    Esse texto já vem no padrão que vai para o grupo:
      Não perca esta oferta grande na SHEIN! ...
      💰Preço[R$..] -20%
      🛒Título do produto
      🎁Cupom 50% OFF para todo Novo Usuário!
      https://onelink.shein.com/..."""
    for n in nos:
        t = n["texto"]
        m = re.search(r"https://onelink\.shein\.com/\S+", t)
        if m:
            titulo = re.search(r"🛒\s*(.+)", t)
            preco = re.search(r"Preço\[(R\$[\d.,]+)\]", t)
            mensagem = t.replace("\u200b", "").replace("\xa0", " ").strip()
            mensagem = "\n".join(l.strip() for l in mensagem.splitlines() if l.strip())
            return {
                "link": m.group(0).strip(),
                "titulo_completo": titulo.group(1).strip() if titulo else "",
                "preco": preco.group(1) if preco else "",
                "mensagem": mensagem,
            }
    return None


def fechar_painel(nos=None):
    """Fecha o painel pelo X (o botão 'voltar' sairia da busca)."""
    nos = nos if nos is not None else tela_atual()
    titulo = achar(nos, contem="Compartilhe para ganhar")
    if titulo:
        tocar(titulo["x2"] - px(0.039), titulo["y1"] - px(0.015))  # o X fica logo acima, à direita
        time.sleep(1.5)


# ----------------------------------------------------------------------------
# Conferência do link (ID da afiliada e ID do produto)
# ----------------------------------------------------------------------------

def conferir_link(link):
    """Abre o link (só lê a página, sem navegador) e devolve koc_id e goods_id."""
    req = urllib.request.Request(link, headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/130.0 Mobile Safari/537.36"})
    for tentativa in range(3):
        try:
            html = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", errors="replace")
            koc = re.search(r"koc_id(?:=|%3D|\\u003d)(\d+)", html)
            goods = re.search(r"goods_id(?:=|%3D|\\u003d)(\d+)", html)
            return (koc.group(1) if koc else None), (goods.group(1) if goods else None)
        except Exception as e:
            print(f"   (falha ao conferir o link, tentando de novo: {e})")
            time.sleep(5)
    return None, None


# ----------------------------------------------------------------------------
# Título curto para a lista
# ----------------------------------------------------------------------------

SUBSTANTIVOS = {
    "vestido", "top", "blusa", "camisa", "camiseta", "regata", "cropped", "calça", "calca", "saia", "short",
    "shorts", "bermuda", "conjunto", "macacão", "macacao", "macaquinho", "body", "blazer", "jaqueta", "casaco",
    "cardigan", "suéter", "sueter", "moletom", "colete", "bolsa", "mochila", "carteira", "sandália", "sandalia",
    "tênis", "tenis", "bota", "sapato", "sapatilha", "chinelo", "colar", "brinco", "brincos", "anel", "anéis",
    "pulseira", "relógio", "relogio", "óculos", "oculos", "cinto", "chapéu", "boné", "biquíni", "biquini",
    "maiô", "maio", "pijama", "lingerie", "sutiã", "calcinha", "meia", "meias", "legging", "corset", "kimono",
    "quimono", "túnica", "tunica", "jardineira", "trench", "tricô", "polo", "1", "2", "3", "4", "5",
}
CORTES = (",", " com ", " para ", " em ", " de manga", " - ", "|", "(")


def titulo_curto(titulo, max_palavras=5):
    t = re.sub(r"\s+", " ", titulo.replace("\xa0", " ")).strip()
    t = re.sub(r"^SHEIN\s+", "", t)  # tira o "SHEIN" do começo
    palavras = t.split(" ")
    # marca = palavras antes do primeiro tipo de peça (no máximo 2)
    marca = []
    for i, p in enumerate(palavras[:3]):
        if p.lower() in SUBSTANTIVOS:
            marca = palavras[:i]
            palavras = palavras[i:]
            break
    resto = " ".join(palavras)
    for c in CORTES:
        pos = resto.lower().find(c)
        if pos > 12:
            resto = resto[:pos]
    pal = resto.split(" ")[:max_palavras]
    while len(pal) > 1 and pal[-1].lower() in ("e", "de", "da", "do", "com", "em", "para", "a", "o", "&"):
        pal.pop()  # não termina o título em "e", "de", "com"...
    resto = " ".join(pal).strip(" ,.-")
    if marca and len(marca) <= 2:
        resto = f"{resto} {' '.join(marca)}"
    return resto[:1].upper() + resto[1:]


# ----------------------------------------------------------------------------
# Progresso e arquivos de saída
# ----------------------------------------------------------------------------

def carregar_progresso():
    if os.path.exists(ARQ_PROGRESSO):
        with open(ARQ_PROGRESSO, encoding="utf-8") as f:
            return json.load(f)
    return {"koc_id": None, "itens": []}


def salvar_progresso(prog):
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    tmp = ARQ_PROGRESSO + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(prog, f, ensure_ascii=False, indent=1)
    os.replace(tmp, ARQ_PROGRESSO)  # troca de uma vez, para não corromper se cair


def slug(txt):
    s = sem_acento(txt).lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def mensagem_do_item(it):
    """Texto no padrão do app. Itens antigos sem o texto salvo são remontados."""
    if it.get("mensagem"):
        return it["mensagem"]
    return ("Não perca esta oferta grande na SHEIN! Economize muito agora!\n"
            f"💰Preço[{it['preco']}]\n🛒{it['titulo_completo']}\n"
            f"🎁Cupom 50% OFF para todo Novo Usuário!\n{it['link']}")


def escrever_lista(caminho, itens):
    formato = CFG.get("formato_saida", "mensagem")
    largura = max(2, len(str(len(itens))))
    with open(caminho, "w", encoding="utf-8") as f:
        for i, it in enumerate(itens, 1):
            if formato == "lista":
                f.write(f"{str(i).zfill(largura)} • {it['titulo_curto']}\n{it['link']}\n\n")
            else:  # padrão: a mensagem completa do app, uma em branco entre elas
                f.write(mensagem_do_item(it) + "\n\n")


def gerar_txts(prog):
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    hoje = date.today().isoformat()
    itens = prog["itens"]
    geral = os.path.join(PASTA_SAIDA, f"links_shein_{hoje}.txt")
    escrever_lista(geral, itens)
    por_cat = {}
    for it in itens:
        por_cat.setdefault(it["categoria"], []).append(it)
    for cat, lista in por_cat.items():
        escrever_lista(os.path.join(PASTA_SAIDA, f"links_{slug(cat)}.txt"), lista)
    return geral


# ----------------------------------------------------------------------------
# Programa principal
# ----------------------------------------------------------------------------

def minerar():
    checar_celular()
    prog = carregar_progresso()
    alvo = int(CFG.get("quantidade_alvo", 300))
    termos = CFG.get("buscas") or ["vestido"]
    koc_esperado = str(CFG.get("koc_id_afiliada") or prog.get("koc_id") or "").strip() or None
    ids_vistos = {it["goods_id"] for it in prog["itens"]}
    titulos_vistos = {it["titulo_lista"] for it in prog["itens"]}
    por_termo = -(-alvo // len(termos))  # divide o alvo entre os termos (arredonda para cima)
    lote = int(CFG.get("descanso_a_cada", 25))
    print(f"Já salvos: {len(prog['itens'])} | alvo: {alvo} | ~{por_termo} por busca")

    rodada = 0
    while len(prog["itens"]) < alvo:
        rodada += 1
        if rodada > 3:
            print("As buscas não renderam mais produtos novos. Acrescente termos no config.")
            break
        for termo in termos:
            feitos_termo = sum(1 for it in prog["itens"] if it["categoria"] == termo)
            meta_termo = por_termo * rodada
            if feitos_termo >= meta_termo or len(prog["itens"]) >= alvo:
                continue
            print(f"\n=== Buscando: {termo} ({feitos_termo}/{meta_termo}) ===")
            pesquisar(termo)
            rolagens_sem_novidade = 0
            falhas = {}
            refeitas = 0
            fila = []  # produtos lidos da tela que ainda vão ganhar link
            while feitos_termo < meta_termo and len(prog["itens"]) < alvo:
                if not fila:
                    # lê a lista uma vez e guarda todos os produtos novos visíveis
                    nos = tela_atual()
                    motivo = bloqueio(nos)
                    if motivo:
                        esperar_pessoa(motivo)
                        continue
                    fila = [c for c in cards_na_tela(nos) if c["titulo"] not in titulos_vistos]
                    if not fila and not achar(nos, texto="Pesquisa"):
                        # saiu da página de resultados (ex.: abriu um produto): volta e refaz a busca
                        refeitas += 1
                        if refeitas > 3:
                            print("   a busca não abriu direito 3 vezes; indo para o próximo termo")
                            break
                        voltar_para_busca(termo)
                        continue
                    if not fila:
                        rolagens_sem_novidade += 1
                        if rolagens_sem_novidade > 4:
                            print("   fim dos resultados desta busca")
                            break
                        rolar_para_baixo()
                        time.sleep(random.uniform(1.5, 2.5))
                        continue
                    rolagens_sem_novidade = 0
                card = fila.pop(0)
                titulos_vistos.add(card["titulo"])
                tocar(*centro(card["botao"]))
                time.sleep(random.uniform(2, 3))
                nos = tela_atual()
                painel = ler_painel(nos)
                if not painel:
                    motivo = bloqueio(nos)
                    if motivo:
                        esperar_pessoa(motivo)
                    falhas[card["titulo"]] = falhas.get(card["titulo"], 0) + 1
                    if falhas[card["titulo"]] < 2:
                        titulos_vistos.discard(card["titulo"])  # tenta de novo uma vez
                    else:
                        print(f"   sem link para: {card['titulo'][:50]} (pulando)")
                    fila = []  # a tela mudou: relê a lista na próxima volta
                    fechar_painel(nos)
                    voltar_para_busca(termo)
                    pausa(2, 4)
                    continue
                koc, goods = conferir_link(painel["link"])
                if not koc or not goods:
                    print(f"   não consegui conferir o link {painel['link']} (pulando)")
                elif koc_esperado is None:
                    koc_esperado = koc
                    print(f"\nID da afiliada detectado no 1º link: koc_id={koc}. "
                          "Confira se é o da conta certa! (fica salvo no progresso)")
                if koc and koc_esperado and koc != koc_esperado:
                    salvar_progresso(prog)
                    sys.exit(f"\nPAREI: o link saiu com outro ID de afiliada (koc_id={koc}, esperado {koc_esperado}).\n"
                             f"Confira a conta logada no app. Link: {painel['link']}")
                fechar_painel(nos)  # pelo X, sem reler a tela
                if koc and goods and goods not in ids_vistos:
                    ids_vistos.add(goods)
                    item = {
                        "goods_id": goods,
                        "titulo_lista": card["titulo"],
                        "titulo_completo": painel["titulo_completo"] or card["titulo"],
                        "titulo_curto": titulo_curto(painel["titulo_completo"] or card["titulo"]),
                        "preco": painel["preco"] or card["preco"],
                        "link": painel["link"],
                        "mensagem": painel["mensagem"],
                        "categoria": termo,
                        "data": date.today().isoformat(),
                    }
                    prog["itens"].append(item)
                    prog["koc_id"] = koc_esperado
                    salvar_progresso(prog)
                    feitos_termo += 1
                    n = len(prog["itens"])
                    print(f"{n:>4} • {item['titulo_curto']} | {item['preco']} | {item['link']}")
                    if n % 50 == 0:
                        gerar_txts(prog)
                        print(f"--- {n} links prontos (arquivos .txt atualizados) ---")
                    if n % lote == 0:
                        descanso = random.uniform(CFG.get("descanso_min_s", 60), CFG.get("descanso_max_s", 120))
                        print(f"   descansando {descanso:.0f} s...")
                        time.sleep(descanso)
                        continue
                elif goods in ids_vistos:
                    print(f"   repetido (produto {goods}), pulando")
                pausa()
            # volta para a Central antes do próximo termo
            tecla(4)
            time.sleep(3)

    geral = gerar_txts(prog)
    print(f"\nPronto! {len(prog['itens'])} links. Arquivo geral: {geral}")
    print(f"Arquivos por busca também estão em: {PASTA_SAIDA}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "txt":
        # só regera os .txt a partir do progresso salvo
        print(gerar_txts(carregar_progresso()))
    else:
        try:
            minerar()
        except KeyboardInterrupt:
            print("\nInterrompido. O progresso está salvo; rode de novo para continuar.")
