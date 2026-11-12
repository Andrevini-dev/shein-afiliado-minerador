# -*- coding: utf-8 -*-
"""
Registrador de links de afiliado SHEIN (modo iPhone / modo agente).

Para quem usa iPhone: um agente (ex.: Codex) controla o app SHEIN no iPhone com a
ferramenta que ele já tem, toca em "Ganhe" e copia o texto do painel
"Compartilhe para ganhar". Este script recebe esse texto, confere o ID da afiliada
(koc_id), tira produtos repetidos e gera os .txt — igual ao minerador do Android.

Exemplos:
  # texto colado pela entrada padrão (pode ter vários produtos de uma vez)
  python registrar.py --pasta C:\\shein-links --categoria vestido < texto.txt

  # texto que está na área de transferência (Windows ou Mac)
  python registrar.py --pasta ~/shein-links --categoria vestido --clipboard

  # quantos já tem e quais títulos já foram (para o agente pular repetidos)
  python registrar.py --pasta ~/shein-links --status

  # só refazer os .txt
  python registrar.py --pasta ~/shein-links --txt

Saída: <pasta>/saida/links_shein_AAAA-MM-DD.txt (geral) e links_<categoria>.txt.
Código de saída 2 = link com OUTRA afiliada (pare e avise a pessoa).
"""

import os
import re
import subprocess
import sys
from datetime import date

# usa as mesmas funções do minerador (conferência, títulos, arquivos de saída)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import minerador as m  # noqa: E402  (lê --pasta e o config ao importar)


def ler_argumento(nome, padrao=None):
    if nome in sys.argv:
        i = sys.argv.index(nome)
        if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
            return sys.argv[i + 1]
        return True
    return padrao


def ler_clipboard():
    """Lê a área de transferência no Windows (PowerShell) ou no Mac (pbpaste)."""
    if sys.platform == "darwin":
        return subprocess.run(["pbpaste"], capture_output=True, text=True).stdout
    if os.name == "nt":
        r = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
                           capture_output=True)
        return r.stdout.decode("utf-8", errors="replace")
    for cmd in (["wl-paste"], ["xclip", "-o", "-selection", "clipboard"]):
        try:
            return subprocess.run(cmd, capture_output=True, text=True).stdout
        except FileNotFoundError:
            continue
    return ""


def separar_blocos(texto):
    """Divide um texto com 1 ou mais mensagens; cada bloco termina no seu link onelink."""
    texto = texto.replace("\u200b", "").replace("\xa0", " ").replace("\r", "")
    blocos, inicio = [], 0
    for achado in re.finditer(r"https://onelink\.shein\.com/\S+", texto):
        bloco = texto[inicio:achado.end()].strip()
        inicio = achado.end()
        # se houver mais de uma mensagem antes do link, fica só a última
        partes = re.split(r"(?=Não perca esta oferta)", bloco)
        blocos.append(partes[-1].strip() if partes[-1].strip() else bloco)
    return blocos


def registrar(texto, categoria):
    prog = m.carregar_progresso()
    koc_esperado = str(m.CFG.get("koc_id_afiliada") or prog.get("koc_id") or "").strip() or None
    ids = {it["goods_id"] for it in prog["itens"]}
    novos = 0
    for bloco in separar_blocos(texto):
        painel = m.ler_painel([{"texto": bloco}])
        if not painel:
            continue
        mensagem = "\n".join(l.strip() for l in bloco.splitlines() if l.strip())
        koc, goods = m.conferir_link(painel["link"])
        if not koc or not goods:
            print(f"NAO CONFERIDO (sem internet ou link inválido): {painel['link']}")
            continue
        if koc_esperado is None:
            koc_esperado = koc
            print(f"ID da afiliada detectado: koc_id={koc} (confirme com a pessoa; fica salvo)")
        if koc != koc_esperado:
            m.salvar_progresso(prog)
            print(f"PAREI: link de OUTRA afiliada (koc_id={koc}, esperado {koc_esperado}): {painel['link']}")
            sys.exit(2)
        if goods in ids:
            print(f"REPETIDO (produto {goods}): {painel['titulo_completo'][:60]}")
            continue
        ids.add(goods)
        titulo = painel["titulo_completo"]
        prog["itens"].append({
            "goods_id": goods,
            "titulo_lista": titulo,
            "titulo_completo": titulo,
            "titulo_curto": m.titulo_curto(titulo),
            "preco": painel["preco"],
            "link": painel["link"],
            "mensagem": mensagem,
            "categoria": categoria,
            "data": date.today().isoformat(),
        })
        prog["koc_id"] = koc_esperado
        m.salvar_progresso(prog)
        novos += 1
        print(f"NOVO {len(prog['itens']):>4} • {m.titulo_curto(titulo)} | {painel['preco']} | {painel['link']}")
    geral = m.gerar_txts(prog)
    print(f"Total: {len(prog['itens'])} links ({novos} novos agora). Arquivo: {geral}")


def status():
    prog = m.carregar_progresso()
    print(f"Total: {len(prog['itens'])} | koc_id: {prog.get('koc_id')}")
    por_cat = {}
    for it in prog["itens"]:
        por_cat[it["categoria"]] = por_cat.get(it["categoria"], 0) + 1
    for cat, n in por_cat.items():
        print(f"  {cat}: {n}")
    print("Títulos já registrados (para pular):")
    for it in prog["itens"]:
        print("  - " + it["titulo_completo"][:80])


if __name__ == "__main__":
    if ler_argumento("--status"):
        status()
    elif ler_argumento("--txt"):
        print(m.gerar_txts(m.carregar_progresso()))
    else:
        categoria = ler_argumento("--categoria", "geral")
        if categoria is True:
            categoria = "geral"
        if ler_argumento("--clipboard"):
            texto = ler_clipboard()
        elif ler_argumento("--arquivo"):
            texto = open(ler_argumento("--arquivo"), encoding="utf-8").read()
        else:
            try:
                sys.stdin.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
            texto = sys.stdin.read()
        if "onelink.shein.com" not in texto:
            sys.exit("Não achei nenhum link onelink.shein.com no texto recebido.")
        registrar(texto, categoria)
