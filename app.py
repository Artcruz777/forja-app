import hashlib
import json
import os
import random
import secrets
import smtplib
import urllib.parse
from datetime import datetime, timedelta
from email.message import EmailMessage

import streamlit as st
import streamlit.components.v1 as components

try:
    import requests
except ImportError:
    requests = None

st.set_page_config(page_title="Treino de Calistenia", page_icon="💪", layout="centered")

HISTORICO_ARQUIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historico_treino.json")
SESSOES_POR_NIVEL = 4  # a cada N treinos concluídos, o app sobe um degrau de dificuldade

TEXTO_POLITICA_PRIVACIDADE = """
**O que coletamos:** nome, email e senha (guardada de forma criptografada,
nunca em texto puro), além do seu histórico de treinos (datas e progressão)
e o status da sua assinatura.

**Peso, altura e idade** são usados só para calcular seu treino na hora —
não ficam salvos em nenhum lugar.

**Onde fica guardado:** seus dados de conta e histórico ficam numa planilha
do Google Sheets, acessível apenas pela conta que administra o FORJA.

**Pagamentos:** processados pela Cakto; não temos acesso ao número do seu
cartão nem dados bancários completos.

**Seus direitos:** você pode pedir a exclusão da sua conta e dos seus dados
a qualquer momento, entrando em contato pelo email de suporte do FORJA.

**Cookies/URL:** não usamos cookies de rastreamento. A sessão de login fica
apenas na memória do navegador enquanto a aba estiver aberta.

_Este é um resumo simples, não um documento jurídico. Se você tiver dúvidas
específicas sobre como seus dados são tratados, entre em contato._
"""

TEXTO_TERMOS_DE_USO = """
**Assinatura:** o FORJA custa R$14,99/mês, com 3 dias de teste
grátis pra novas contas. A cobrança é recorrente e automática (via Cakto),
até você cancelar.

**Cancelamento:** pode ser feito a qualquer momento diretamente na Cakto
(no link de gerenciamento da assinatura que você recebeu por email na
compra). Após cancelar, você mantém acesso até o fim do período já pago.

**Reembolso:** segue a política padrão da Cakto para o período de
arrependimento previsto em lei (7 dias corridos a partir da compra).

**Uso aceitável:** sua conta é pessoal e intransferível. Não compartilhe
seu login com outras pessoas.

**Isenção de responsabilidade sobre saúde:** o FORJA gera sugestões de
treino com base nas informações que você fornece, mas **não substitui
avaliação médica ou de um profissional de educação física**. Consulte um
médico antes de iniciar qualquer programa de exercícios, especialmente se
você tiver condições de saúde preexistentes, estiver grávida, ou sentir
qualquer dor incomum durante o treino — nesse caso, pare imediatamente.

**Limitação de responsabilidade:** o uso do treino gerado é por sua conta
e risco. O FORJA não se responsabiliza por lesões decorrentes da execução
incorreta dos exercícios ou do não seguimento desta recomendação médica.

_Este é um resumo simples, não um documento jurídico completo._
"""

# ---------------------------------------------------------------------------
# VISUAL
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap');

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
.stApp { background-color: #12181f; }
h1, h2, h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 0.5px; color: #EDE8DD !important; }
p, span, label, .stMarkdown, div { color: #EDE8DD; }
.stCaption, small { color: #a8a396 !important; }

.forja-header { display:flex; align-items:center; justify-content:space-between; gap:14px; margin-bottom:2px; }
.forja-brand { display:flex; align-items:center; gap:14px; }
.forja-mark { width:38px; height:38px; flex:none; border:2px solid #E8A33D; display:flex; align-items:center;
  justify-content:center; font-family:'Bebas Neue',sans-serif; font-size:18px; color:#E8A33D; transform:rotate(45deg); }
.forja-mark span { transform:rotate(-45deg); display:block; }
.forja-profile { display:flex; align-items:center; gap:8px; font-family:'JetBrains Mono',monospace; font-size:12px;
  color:#a8a396; }
.forja-profile .patente-emoji { font-size:17px; }
.forja-profile .nome { color:#EDE8DD; font-weight:600; }
.forja-profile .patente-nome { color:#E8A33D; }

div[data-testid="stForm"] { background:#1b232c; border:1px solid #2c3542; border-radius:8px; padding:20px; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] { background:#1b232c; border-radius:5px; color:#a8a396; }
.stTabs [aria-selected="true"] { color:#E8A33D !important; border-bottom:2px solid #E8A33D !important; }

.ex-card { background:#1b232c; border:1px solid #2c3542; border-radius:6px; padding:14px 16px; margin-bottom:10px; }
.ex-top { display:flex; justify-content:space-between; align-items:baseline; }
.ex-nome { font-size:15.5px; font-weight:600; color:#EDE8DD; }
.ex-nivel { font-family:'JetBrains Mono',monospace; font-size:11px; color:#C1502E; margin-left:6px; }
.ex-scheme { font-family:'JetBrains Mono',monospace; font-size:13px; color:#E8A33D; white-space:nowrap; }
.ex-dica { font-size:12.5px; color:#a8a396; margin-top:6px; }
.ex-link { font-size:12px; color:#E8A33D; text-decoration:none; }

.grp-label { font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:1.5px; color:#4A5560;
  text-transform:uppercase; margin:18px 0 8px; }

.pill { font-family:'JetBrains Mono',monospace; font-size:11px; color:#a8a396; border:1px solid #2c3542;
  padding:5px 10px; border-radius:20px; display:inline-block; margin-right:6px; }

/* cards de card numerado (containers com borda) */
div[data-testid="stVerticalBlockBorderWrapper"] { background:#1b232c; border:1px solid #2c3542 !important;
  border-radius:6px; }
.onb-eyebrow { font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:2px; color:#E8A33D;
  text-transform:uppercase; margin-bottom:10px; }
.onb-sublabel { font-size:13px; color:#a8a396; margin:14px 0 8px; }

/* botões de opção estilo card */
div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button {
  width:100%; min-height:56px; background:#232d38; border:1px solid #2c3542; border-radius:5px;
  color:#EDE8DD; font-family:'Inter',sans-serif; font-size:13.5px; font-weight:600;
  padding:10px 8px; white-space:normal; line-height:1.3;
}
div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button:hover {
  border-color:#4A5560; color:#EDE8DD;
}
div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button[kind="primary"] {
  background:rgba(232,163,61,0.12); border-color:#E8A33D !important; color:#E8A33D !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] .stCaption {
  text-align:center; margin-top:-8px; margin-bottom:6px; font-size:11px !important;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# PERSISTÊNCIA (progressão automática entre sessões)
# ---------------------------------------------------------------------------
COLUNAS_HISTORICO = ["email", "sessoes_concluidas", "ultimo_treino", "datas_treinos"]


@st.cache_data(ttl=15, show_spinner=False)
def carregar_historico():
    if _sheets_disponivel():
        aba = _obter_worksheet("historico", COLUNAS_HISTORICO)
        registros = aba.get_all_records()
        historico = {}
        for linha in registros:
            email = str(linha.get("email", "")).strip().lower()
            if email:
                datas_str = linha.get("datas_treinos", "") or ""
                historico[email] = {
                    "sessoes_concluidas": int(linha.get("sessoes_concluidas") or 0),
                    "ultimo_treino": linha.get("ultimo_treino") or None,
                    "datas_treinos": [d for d in str(datas_str).split(",") if d],
                }
        return historico

    if os.path.exists(HISTORICO_ARQUIVO):
        try:
            with open(HISTORICO_ARQUIVO, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def salvar_historico(historico):
    if _sheets_disponivel():
        aba = _obter_worksheet("historico", COLUNAS_HISTORICO)
        linhas = [COLUNAS_HISTORICO]
        for email, dados in historico.items():
            linhas.append([
                email,
                str(dados.get("sessoes_concluidas", 0)),
                dados.get("ultimo_treino") or "",
                ",".join(dados.get("datas_treinos", [])),
            ])
        aba.clear()
        aba.update(linhas)
        carregar_historico.clear()
        return

    with open(HISTORICO_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)
    carregar_historico.clear()


def obter_perfil(historico, email):
    return historico.get(email, {"sessoes_concluidas": 0, "ultimo_treino": None, "datas_treinos": []})


def registrar_sessao_concluida(email):
    historico = carregar_historico()
    perfil = obter_perfil(historico, email)
    perfil["sessoes_concluidas"] += 1
    perfil["ultimo_treino"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    hoje_str = datetime.now().strftime("%Y-%m-%d")
    datas = perfil.get("datas_treinos", [])
    if hoje_str not in datas:
        datas.append(hoje_str)
    perfil["datas_treinos"] = datas
    historico[email] = perfil
    salvar_historico(historico)
    return perfil


def calcular_streak(datas_treinos):
    """Retorna (streak_atual, melhor_streak) a partir de uma lista de datas
    no formato 'YYYY-MM-DD'."""
    if not datas_treinos:
        return 0, 0
    dias = sorted({datetime.strptime(d, "%Y-%m-%d").date() for d in datas_treinos})
    melhor = 1
    sequencia = 1
    for i in range(1, len(dias)):
        if (dias[i] - dias[i - 1]).days == 1:
            sequencia += 1
        else:
            melhor = max(melhor, sequencia)
            sequencia = 1
    melhor = max(melhor, sequencia)

    hoje = datetime.now().date()
    if dias[-1] not in (hoje, hoje - timedelta(days=1)):
        return 0, melhor

    streak_atual = 1
    for i in range(len(dias) - 1, 0, -1):
        if (dias[i] - dias[i - 1]).days == 1:
            streak_atual += 1
        else:
            break
    return streak_atual, melhor


PATENTES = [
    (0, "Ferro", "🔩", "recém-chegado à forja"),
    (5, "Bronze", "🥉", "já sente o calor do treino"),
    (15, "Aço", "⚙️", "treino virou rotina"),
    (30, "Titânio", "💠", "disciplina de verdade"),
    (60, "Lenda", "🏆", "poucos chegam aqui"),
]


def calcular_patente(dias_treinados):
    """Retorna (patente_atual, proxima_patente) com base em quantos dias
    diferentes a pessoa já treinou. proxima_patente é None se já estiver
    na patente máxima."""
    atual = PATENTES[0]
    proxima = None
    for limite, nome, emoji, desc in PATENTES:
        if dias_treinados >= limite:
            atual = (limite, nome, emoji, desc)
        else:
            proxima = (limite, nome, emoji, desc)
            break
    return atual, proxima


CONQUISTAS_DISPONIVEIS = [
    ("primeira_semana", "🗓️", "Primeira semana", lambda p, streak_atual, melhor_streak: len(p.get("datas_treinos", [])) >= 7),
    ("primeiro_mes", "📅", "Primeiro mês", lambda p, streak_atual, melhor_streak: len(p.get("datas_treinos", [])) >= 30),
    ("sequencia_7", "🔥", "7 dias seguidos", lambda p, streak_atual, melhor_streak: melhor_streak >= 7),
    ("cem_treinos", "💯", "100 treinos", lambda p, streak_atual, melhor_streak: p.get("sessoes_concluidas", 0) >= 100),
    ("fim_de_semana", "🏋️", "Guerreiro de fim de semana",
     lambda p, streak_atual, melhor_streak: any(
         datetime.strptime(d, "%Y-%m-%d").weekday() >= 5 for d in p.get("datas_treinos", [])
     )),
]


def calcular_conquistas(perfil):
    _, melhor_streak = calcular_streak(perfil.get("datas_treinos", []))
    streak_atual, _ = calcular_streak(perfil.get("datas_treinos", []))
    conquistadas = []
    for chave, emoji, titulo, condicao in CONQUISTAS_DISPONIVEIS:
        if condicao(perfil, streak_atual, melhor_streak):
            conquistadas.append((emoji, titulo))
    return conquistadas


def montar_cartao_patente(dias_treinados):
    (limite_atual, nome_atual, emoji_atual, desc_atual), proxima = calcular_patente(dias_treinados)
    if proxima:
        limite_prox, nome_prox, emoji_prox, _ = proxima
        faltam = limite_prox - dias_treinados
        progresso = (dias_treinados - limite_atual) / (limite_prox - limite_atual)
        rodape = f"faltam {faltam} dia(s) treinados pra virar {nome_prox} {emoji_prox}"
    else:
        progresso = 1.0
        rodape = "patente máxima — você é uma lenda no FORJA"

    return f"""
    <div class="card" style="text-align:center;">
      <div style="font-size:40px;">{emoji_atual}</div>
      <div style="font-family:'Bebas Neue',sans-serif;font-size:24px;color:#E8A33D;letter-spacing:1px;">
        {nome_atual.upper()}
      </div>
      <div style="font-size:12px;color:#a8a396;margin-bottom:10px;">{desc_atual}</div>
      <div style="background:#2c3542;border-radius:3px;height:6px;overflow:hidden;margin-bottom:8px;">
        <div style="background:#E8A33D;height:100%;width:{progresso*100:.0f}%;"></div>
      </div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:10.5px;color:#4A5560;">{rodape}</div>
    </div>
    """


def _carregar_fonte(negrito, tamanho):
    caminhos = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if negrito
        else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    from PIL import ImageFont
    for caminho in caminhos:
        try:
            return ImageFont.truetype(caminho, tamanho)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def montar_imagem_patente(nome, nome_patente, streak_atual, melhor_streak, dias_treinados, sessoes_concluidas):
    """Gera um card quadrado (1080x1080) pra compartilhar nas redes sociais,
    mostrando a patente atual e as estatísticas de treino."""
    from PIL import Image, ImageDraw
    import io

    LARGURA = ALTURA = 1080
    INK = (18, 24, 31)
    INK_2 = (27, 35, 44)
    BONE = (237, 232, 221)
    BONE_DIM = (168, 163, 150)
    EMBER = (232, 163, 61)
    LINE = (44, 53, 66)

    img = Image.new("RGB", (LARGURA, ALTURA), INK)
    draw = ImageDraw.Draw(img)

    fonte_marca = _carregar_fonte(True, 34)
    fonte_patente = _carregar_fonte(True, 96)
    fonte_nome = _carregar_fonte(True, 46)
    fonte_label = _carregar_fonte(False, 26)
    fonte_stat_num = _carregar_fonte(True, 58)
    fonte_stat_label = _carregar_fonte(False, 22)

    # marca FORJA (losango + texto) no topo
    cx, cy, r = 90, 90, 26
    draw.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], outline=EMBER, width=4)
    draw.text((cx, cy), "F", font=_carregar_fonte(True, 24), fill=EMBER, anchor="mm")
    draw.text((140, 90), "FORJA", font=fonte_marca, fill=BONE, anchor="lm")

    # patente em destaque, centralizada
    draw.text((LARGURA / 2, 430), nome_patente.upper(), font=fonte_patente, fill=EMBER, anchor="mm")
    draw.text((LARGURA / 2, 500), nome, font=fonte_nome, fill=BONE, anchor="mm")

    # cartão de estatísticas
    topo_card = 620
    draw.rounded_rectangle([(70, topo_card), (LARGURA - 70, topo_card + 300)], radius=18, fill=INK_2,
                            outline=LINE, width=2)
    stats = [
        (f"{streak_atual}", "SEQUÊNCIA ATUAL"),
        (f"{melhor_streak}", "MELHOR SEQUÊNCIA"),
        (f"{dias_treinados}", "DIAS TREINADOS"),
    ]
    largura_col = (LARGURA - 140) / 3
    for i, (numero, rotulo) in enumerate(stats):
        cx_stat = 70 + largura_col * i + largura_col / 2
        draw.text((cx_stat, topo_card + 110), numero, font=fonte_stat_num, fill=EMBER, anchor="mm")
        draw.text((cx_stat, topo_card + 175), rotulo, font=fonte_stat_label, fill=BONE_DIM, anchor="mm")

    draw.line([(70, topo_card + 220), (LARGURA - 70, topo_card + 220)], fill=LINE, width=2)
    draw.text((LARGURA / 2, topo_card + 260), f"{sessoes_concluidas} treinos concluídos no total",
               font=fonte_label, fill=BONE_DIM, anchor="mm")

    draw.text((LARGURA / 2, ALTURA - 60), "forjaapp.com.br", font=fonte_label, fill=BONE_DIM, anchor="mm")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def montar_heatmap_treinos(datas_treinos, semanas=10):
    """Monta uma grade tipo 'GitHub contributions' com os últimos dias,
    marcando em qual dia a pessoa treinou."""
    dias_totais = semanas * 7
    hoje = datetime.now().date()
    datas_set = set(datas_treinos)
    inicio = hoje - timedelta(days=dias_totais - 1)
    celulas = []
    for i in range(dias_totais):
        dia = inicio + timedelta(days=i)
        treinou = dia.strftime("%Y-%m-%d") in datas_set
        cor = "#E8A33D" if treinou else "#232d38"
        celulas.append(
            f'<div title="{dia.strftime("%d/%m")}" '
            f'style="width:11px;height:11px;border-radius:2px;background:{cor};"></div>'
        )
    return (
        '<div style="display:grid;grid-template-rows:repeat(7,12px);grid-auto-flow:column;gap:3px;">'
        + "".join(celulas) + "</div>"
    )


COLUNAS_FEED = ["id", "email", "nome", "texto", "data", "streak", "curtidas"]
FEED_ARQUIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feed.json")


@st.cache_data(ttl=15, show_spinner=False)
def carregar_feed():
    if _sheets_disponivel():
        aba = _obter_worksheet("feed", COLUNAS_FEED)
        registros = aba.get_all_records()
        posts = []
        for linha in registros:
            if str(linha.get("id", "")).strip():
                posts.append({
                    "id": str(linha.get("id", "")),
                    "email": linha.get("email", ""),
                    "nome": linha.get("nome", ""),
                    "texto": linha.get("texto", ""),
                    "data": linha.get("data", ""),
                    "streak": linha.get("streak", ""),
                    "curtidas": [e for e in str(linha.get("curtidas", "")).split(",") if e],
                })
        return list(reversed(posts))

    if os.path.exists(FEED_ARQUIVO):
        try:
            with open(FEED_ARQUIVO, "r", encoding="utf-8") as f:
                return list(reversed(json.load(f)))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _salvar_feed_bruto(posts):
    if _sheets_disponivel():
        aba = _obter_worksheet("feed", COLUNAS_FEED)
        linhas = [COLUNAS_FEED]
        for post in posts:
            linhas.append([
                post["id"], post["email"], post["nome"], post["texto"], post["data"],
                str(post.get("streak", "")), ",".join(post.get("curtidas", [])),
            ])
        aba.clear()
        aba.update(linhas)
        carregar_feed.clear()
        return
    with open(FEED_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    carregar_feed.clear()


def publicar_no_feed(email, nome, texto, streak):
    texto = texto.strip()
    if not texto:
        return False
    posts = list(reversed(carregar_feed()))  # volta pra ordem cronológica de gravação
    posts.append({
        "id": secrets.token_hex(6),
        "email": email,
        "nome": nome,
        "texto": texto[:280],
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "streak": streak,
        "curtidas": [],
    })
    _salvar_feed_bruto(posts)
    return True


def curtir_post(post_id, email):
    posts = list(reversed(carregar_feed()))
    for post in posts:
        if post["id"] == post_id:
            if email in post["curtidas"]:
                post["curtidas"].remove(email)
            else:
                post["curtidas"].append(email)
            break
    _salvar_feed_bruto(posts)


# ---------------------------------------------------------------------------
# CONTAS DE USUÁRIO + ASSINATURA — guardado no Google Sheets
# ---------------------------------------------------------------------------
USUARIOS_ARQUIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usuarios.json")
COLUNAS_USUARIOS = ["email", "senha_hash", "senha_salt", "nome", "assinatura_status", "assinatura_valido_ate",
                     "data_cadastro", "reset_codigo", "reset_expira", "meses_pagos"]



def _sheets_disponivel():
    return "gcp_service_account" in st.secrets and "planilha_codigos_id" in st.secrets


@st.cache_resource(show_spinner=False)
def _conectar_planilha():
    """Abre a conexão com a planilha UMA vez só e guarda em cache — abrir a
    planilha de novo a cada chamada é o que estourava a cota de leitura da
    API do Google."""
    import gspread
    from google.oauth2.service_account import Credentials

    escopos = ["https://www.googleapis.com/auth/spreadsheets"]
    credenciais = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=escopos)
    cliente = gspread.authorize(credenciais)
    return cliente.open_by_key(st.secrets["planilha_codigos_id"])


def _obter_worksheet(nome_aba, colunas):
    """Pega a aba certa dentro da planilha (já conectada e em cache). Cria
    a aba com o cabeçalho certo se ela ainda não existir."""
    import gspread

    planilha = _conectar_planilha()
    try:
        aba = planilha.worksheet(nome_aba)
    except gspread.WorksheetNotFound:
        aba = planilha.add_worksheet(nome_aba, rows=500, cols=len(colunas))
        aba.update([colunas])
    return aba


def _gerar_hash_senha(senha, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    hash_ = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(salt), 200_000).hex()
    return hash_, salt


def _verificar_senha(senha, hash_salvo, salt):
    hash_calc, _ = _gerar_hash_senha(senha, salt)
    return hash_calc == hash_salvo


@st.cache_data(ttl=15, show_spinner=False)
def carregar_usuarios():
    if _sheets_disponivel():
        aba = _obter_worksheet("usuarios", COLUNAS_USUARIOS)
        registros = aba.get_all_records()
        usuarios = {}
        for linha in registros:
            email = str(linha.get("email", "")).strip().lower()
            if email:
                usuarios[email] = {c: linha.get(c, "") for c in COLUNAS_USUARIOS if c != "email"}
        return usuarios

    if os.path.exists(USUARIOS_ARQUIVO):
        try:
            with open(USUARIOS_ARQUIVO, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def salvar_usuarios(usuarios):
    if _sheets_disponivel():
        aba = _obter_worksheet("usuarios", COLUNAS_USUARIOS)
        linhas = [COLUNAS_USUARIOS]
        for email, dados in usuarios.items():
            linhas.append([email] + [str(dados.get(c, "")) for c in COLUNAS_USUARIOS if c != "email"])
        aba.clear()
        aba.update(linhas)
        carregar_usuarios.clear()
        return

    with open(USUARIOS_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=2)
    carregar_usuarios.clear()


DIAS_TESTE_GRATIS = 3
DIAS_TOLERANCIA = 3
PRECO_MENSAL = "R$14,99"


def criar_conta(email, senha, nome):
    email = email.strip().lower()
    if not email or "@" not in email:
        return False, "Digite um email válido."
    usuarios = carregar_usuarios()
    if email in usuarios:
        return False, "Esse email já tem cadastro. Faça login na aba ao lado."
    hash_, salt = _gerar_hash_senha(senha)
    validade_teste = (datetime.now() + timedelta(days=DIAS_TESTE_GRATIS)).strftime("%Y-%m-%d")
    usuarios[email] = {
        "senha_hash": hash_,
        "senha_salt": salt,
        "nome": nome.strip(),
        "assinatura_status": "teste",
        "assinatura_valido_ate": validade_teste,
        "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "reset_codigo": "",
        "reset_expira": "",
        "meses_pagos": "0",
    }
    salvar_usuarios(usuarios)
    return True, f"Conta criada! Você já tem {DIAS_TESTE_GRATIS} dias de teste grátis. Entre na aba \"Entrar\"."


def autenticar(email, senha):
    email = email.strip().lower()
    usuarios = carregar_usuarios()
    if email not in usuarios:
        return False, "Email não encontrado. Crie uma conta na aba ao lado.", None
    dados = usuarios[email]
    if not _verificar_senha(senha, dados.get("senha_hash", ""), dados.get("senha_salt", "")):
        return False, "Senha incorreta.", None
    return True, "Login feito!", {"email": email, **dados}


def status_acesso(usuario):
    """Retorna um dict descrevendo se o acesso está liberado agora, considerando
    teste grátis, assinatura ativa e o período de tolerância após o vencimento."""
    status = usuario.get("assinatura_status")
    validade_str = usuario.get("assinatura_valido_ate")
    if status not in ("teste", "ativa") or not validade_str:
        return {"liberado": False, "motivo": status or "sem_assinatura", "dias_restantes": 0, "em_tolerancia": False}

    try:
        validade = datetime.strptime(str(validade_str), "%Y-%m-%d").date()
    except ValueError:
        return {"liberado": False, "motivo": "sem_assinatura", "dias_restantes": 0, "em_tolerancia": False}

    hoje = datetime.now().date()
    fim_tolerancia = validade + timedelta(days=DIAS_TOLERANCIA)

    if hoje <= validade:
        return {"liberado": True, "motivo": status, "dias_restantes": (validade - hoje).days, "em_tolerancia": False}
    if hoje <= fim_tolerancia:
        return {"liberado": True, "motivo": status, "dias_restantes": (fim_tolerancia - hoje).days, "em_tolerancia": True}
    return {"liberado": False, "motivo": "expirado", "dias_restantes": 0, "em_tolerancia": False}


def assinatura_esta_ativa(usuario):
    return status_acesso(usuario)["liberado"]


def recarregar_usuario_logado():
    """Relê os dados desse usuário na planilha — usado depois que a pessoa
    volta do checkout, pra ver se o webhook já ativou a assinatura dela."""
    email = st.session_state["usuario_logado"]["email"]
    carregar_usuarios.clear()  # força ler o dado mais atual, ignorando o cache
    usuarios = carregar_usuarios()
    if email in usuarios:
        st.session_state["usuario_logado"] = {"email": email, **usuarios[email]}


def _email_configurado():
    return "email_remetente" in st.secrets and "email_senha_app" in st.secrets


def _enviar_email(destinatario, assunto, corpo):
    if not _email_configurado():
        return False
    remetente = st.secrets["email_remetente"]
    senha_app = st.secrets["email_senha_app"]
    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = remetente
    msg["To"] = destinatario
    msg.set_content(corpo)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(remetente, senha_app)
            servidor.send_message(msg)
        return True
    except Exception:
        return False


def solicitar_redefinicao_senha(email):
    """Gera um código de 6 dígitos, válido por 15 minutos, e envia por email.
    Sempre retorna a mesma mensagem (exista ou não a conta), pra não revelar
    quais emails têm cadastro."""
    email = email.strip().lower()
    mensagem_padrao = "Se esse email tiver cadastro, enviamos um código de redefinição para ele."
    usuarios = carregar_usuarios()
    if email not in usuarios:
        return True, mensagem_padrao
    codigo = f"{secrets.randbelow(1000000):06d}"
    expira = (datetime.now() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    usuarios[email]["reset_codigo"] = codigo
    usuarios[email]["reset_expira"] = expira
    salvar_usuarios(usuarios)
    enviado = _enviar_email(
        email,
        "Código para redefinir sua senha — FORJA",
        f"Seu código de redefinição de senha é: {codigo}\n\n"
        f"Ele vale por 15 minutos. Se você não pediu isso, pode ignorar este email.",
    )
    if not enviado:
        return False, "Não consegui enviar o email agora. Tente de novo em instantes."
    return True, mensagem_padrao


def redefinir_senha(email, codigo, nova_senha):
    email = email.strip().lower()
    usuarios = carregar_usuarios()
    if email not in usuarios:
        return False, "Código inválido ou expirado."
    dados = usuarios[email]
    codigo_salvo = str(dados.get("reset_codigo", "") or "")
    expira_str = dados.get("reset_expira", "") or ""
    if not codigo_salvo or codigo.strip() != codigo_salvo:
        return False, "Código inválido ou expirado."
    try:
        expira = datetime.strptime(expira_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return False, "Código inválido ou expirado."
    if datetime.now() > expira:
        return False, "Esse código expirou. Peça um novo."
    if len(nova_senha) < 6:
        return False, "A nova senha precisa ter pelo menos 6 caracteres."
    hash_, salt = _gerar_hash_senha(nova_senha)
    dados["senha_hash"] = hash_
    dados["senha_salt"] = salt
    dados["reset_codigo"] = ""
    dados["reset_expira"] = ""
    usuarios[email] = dados
    salvar_usuarios(usuarios)
    return True, "Senha redefinida! Já pode entrar com a senha nova."


# ---------------------------------------------------------------------------
# BANCO DE EXERCÍCIOS (com dica de execução para cada um)
# ---------------------------------------------------------------------------
EXERCICIOS = {
    "peito_ombro_triceps": [
        {"nome": "Flexão inclinada (mãos numa cadeira)", "nivel": 1, "so_academia": False,
         "dica": "Mantenha o corpo reto da cabeça aos pés, sem deixar o quadril cair."},
        {"nome": "Flexão de joelhos", "nivel": 1, "so_academia": False,
         "dica": "Cotovelos a cerca de 45° do tronco, desça até o peito quase tocar o chão."},
        {"nome": "Flexão de braço tradicional", "nivel": 2, "so_academia": False,
         "dica": "Mãos um pouco mais largas que os ombros, core contraído o tempo todo."},
        {"nome": "Flexão com pés elevados", "nivel": 2, "so_academia": False,
         "dica": "Pés numa cadeira ou sofá; quanto mais alto, mais peso vai para o ombro."},
        {"nome": "Fundos em banco/cadeira (dips)", "nivel": 2, "so_academia": False,
         "dica": "Cotovelos apontando para trás, não para os lados, para poupar o ombro."},
        {"nome": "Flexão diamante", "nivel": 3, "so_academia": False,
         "dica": "Mãos formando um triângulo sob o peito; foco total no tríceps."},
        {"nome": "Flexão arqueiro", "nivel": 3, "so_academia": False,
         "dica": "Desloque o peso para um braço enquanto o outro fica quase estendido ao lado."},
        {"nome": "Apoio de pino na parede (tempo)", "nivel": 3, "so_academia": False, "cronometrado": True,
         "dica": "Mãos afastadas na largura dos ombros, olhar fixo no chão para manter o equilíbrio."},
        {"nome": "Flexão pike (ombro)", "nivel": 2, "so_academia": False,
         "dica": "Quadril elevado formando um V invertido; desça a cabeça em direção ao chão."},
        {"nome": "Supino reto com barra", "nivel": 2, "so_academia": True,
         "dica": "Escápulas retraídas e pés firmes no chão durante todo o movimento."},
        {"nome": "Desenvolvimento com halteres", "nivel": 2, "so_academia": True,
         "dica": "Não trave os cotovelos no topo; mantenha leve tensão constante."},
        {"nome": "Tríceps na polia", "nivel": 1, "so_academia": True,
         "dica": "Cotovelos colados ao corpo, só o antebraço se movimenta."},
        {"nome": "Supino com halteres (em casa)", "nivel": 2, "so_academia": False, "equip_casa": "peso",
         "dica": "Deitado num banco ou no chão, desça os halteres controlado até a altura do peito."},
        {"nome": "Desenvolvimento com halteres (em casa)", "nivel": 2, "so_academia": False, "equip_casa": "peso",
         "dica": "Sentado ou em pé, empurre os halteres para cima sem travar o cotovelo no topo."},
        {"nome": "Tríceps francês com halter", "nivel": 2, "so_academia": False, "equip_casa": "peso",
         "dica": "Cotovelos apontando pro teto, só o antebraço se movimenta atrás da cabeça."},
    ],
    "costas_biceps": [
        {"nome": "Remada australiana (mesa firme)", "nivel": 1, "so_academia": False,
         "dica": "Corpo reto e puxe o peito em direção à mesa, apertando as escápulas."},
        {"nome": "Barra fixa negativa (descer devagar)", "nivel": 1, "so_academia": False, "equip_casa": "bar",
         "dica": "Suba com apoio dos pés e desça sozinho o mais devagar possível."},
        {"nome": "Barra fixa", "nivel": 2, "so_academia": False, "equip_casa": "bar",
         "dica": "Puxe com os cotovelos para baixo e para trás, evitando balançar o corpo."},
        {"nome": "Barra fixa supinada", "nivel": 3, "so_academia": False, "equip_casa": "bar",
         "dica": "Pegada com as palmas viradas para você; recruta mais o bíceps."},
        {"nome": "Barra fixa arquer", "nivel": 3, "so_academia": False, "equip_casa": "bar",
         "dica": "Puxe deslocando o peso para um lado, o outro braço fica quase estendido."},
        {"nome": "Remada invertida com toalha na porta", "nivel": 1, "so_academia": False,
         "dica": "Prenda a toalha numa porta firme e puxe o peito em direção às mãos."},
        {"nome": "Puxada alta (pulley)", "nivel": 1, "so_academia": True,
         "dica": "Puxe a barra até a altura do queixo, sem jogar o corpo para trás."},
        {"nome": "Remada baixa (cabo)", "nivel": 2, "so_academia": True,
         "dica": "Tronco ereto, puxe o cabo até a barriga apertando as costas."},
        {"nome": "Rosca direta com barra", "nivel": 2, "so_academia": True,
         "dica": "Cotovelos fixos ao lado do corpo, sem balançar o tronco."},
        {"nome": "Remada curvada com halteres (em casa)", "nivel": 2, "so_academia": False, "equip_casa": "peso",
         "dica": "Tronco inclinado à frente, puxe os halteres em direção à cintura apertando as costas."},
        {"nome": "Rosca direta com halteres (em casa)", "nivel": 2, "so_academia": False, "equip_casa": "peso",
         "dica": "Cotovelos fixos ao lado do corpo, sem balançar o tronco pra ajudar o movimento."},
    ],
    "pernas": [
        {"nome": "Agachamento livre", "nivel": 1, "so_academia": False,
         "dica": "Joelhos seguindo a direção dos pés, quadril descendo como se fosse sentar."},
        {"nome": "Afundo (passada)", "nivel": 1, "so_academia": False,
         "dica": "Joelho de trás quase tocando o chão, tronco ereto."},
        {"nome": "Elevação de panturrilha", "nivel": 1, "so_academia": False,
         "dica": "Suba na ponta dos pés e desça controlado, sem pressa."},
        {"nome": "Ponte de glúteo", "nivel": 1, "so_academia": False,
         "dica": "Aperte o glúteo no topo do movimento por um segundo antes de descer."},
        {"nome": "Agachamento búlgaro (pé na cadeira)", "nivel": 2, "so_academia": False,
         "dica": "Pé de trás apoiado numa cadeira, desça reto para baixo com a perna da frente."},
        {"nome": "Afundo com salto", "nivel": 2, "so_academia": False,
         "dica": "Troque as pernas no ar; aterrisse suave, dobrando o joelho."},
        {"nome": "Agachamento sumô", "nivel": 1, "so_academia": False,
         "dica": "Pés bem afastados, pontas para fora, foco em glúteo e interno da coxa."},
        {"nome": "Agachamento pistol assistido", "nivel": 3, "so_academia": False,
         "dica": "Segure em algo à frente para ajudar o equilíbrio enquanto desce numa perna só."},
        {"nome": "Agachamento livre com barra", "nivel": 2, "so_academia": True,
         "dica": "Barra apoiada no trapézio, core travado, desça controlado."},
        {"nome": "Leg press", "nivel": 1, "so_academia": True,
         "dica": "Não trave os joelhos no topo; desça até 90° no joelho."},
        {"nome": "Cadeira extensora", "nivel": 1, "so_academia": True,
         "dica": "Movimento controlado, sem jogar o peso com impulso."},
        {"nome": "Mesa flexora", "nivel": 1, "so_academia": True,
         "dica": "Quadril colado no banco durante toda a execução."},
        {"nome": "Agachamento com halteres (em casa)", "nivel": 2, "so_academia": False, "equip_casa": "peso",
         "dica": "Halteres ao lado do corpo, desça controlado como no agachamento livre."},
        {"nome": "Afundo com halteres (em casa)", "nivel": 2, "so_academia": False, "equip_casa": "peso",
         "dica": "Halteres ao lado do corpo, joelho de trás quase tocando o chão."},
        {"nome": "Stiff com halteres (em casa)", "nivel": 2, "so_academia": False, "equip_casa": "peso",
         "dica": "Pernas quase esticadas, desça os halteres deslizando perto das canelas, costas retas."},
    ],
    "core": [
        {"nome": "Prancha abdominal", "nivel": 1, "so_academia": False, "cronometrado": True,
         "dica": "Corpo em linha reta, sem deixar o quadril subir ou cair."},
        {"nome": "Prancha lateral", "nivel": 1, "so_academia": False, "cronometrado": True,
         "dica": "Quadril elevado e alinhado, cotovelo bem abaixo do ombro."},
        {"nome": "Abdominal bicicleta", "nivel": 1, "so_academia": False,
         "dica": "Cotovelo tocando o joelho oposto, sem puxar o pescoço com as mãos."},
        {"nome": "Elevação de pernas deitado", "nivel": 2, "so_academia": False,
         "dica": "Lombar sempre apoiada no chão; se doer nas costas, dobre um pouco os joelhos."},
        {"nome": "Mountain climber", "nivel": 2, "so_academia": False, "cronometrado": True,
         "dica": "Quadril baixo e estável, joelhos vindo até perto do peito rápido."},
        {"nome": "Prancha com toque no ombro", "nivel": 2, "so_academia": False, "cronometrado": True,
         "dica": "Quadril o mais parado possível enquanto alterna as mãos tocando o ombro."},
        {"nome": "Dragon flag assistido", "nivel": 3, "so_academia": False,
         "dica": "Segure firme atrás da cabeça e desça o corpo reto o mais devagar possível."},
    ],
    "cardio_saude": [
        {"nome": "Polichinelo", "nivel": 1, "so_academia": False, "cronometrado": True,
         "dica": "Ritmo constante, aterrissagem leve nos pés."},
        {"nome": "Corrida estacionária", "nivel": 1, "so_academia": False, "cronometrado": True,
         "dica": "Joelhos altos, braços acompanhando o ritmo das pernas."},
        {"nome": "Burpee", "nivel": 2, "so_academia": False, "cronometrado": True,
         "dica": "Agachar, prancha, flexão opcional, salto; ritmo constante mais importante que velocidade."},
        {"nome": "Mobilidade de quadril e ombro", "nivel": 1, "so_academia": False, "cronometrado": True,
         "dica": "Movimentos amplos e lentos, sem forçar além do conforto."},
        {"nome": "Escalador lateral", "nivel": 2, "so_academia": False, "cronometrado": True,
         "dica": "Passadas largas de um lado para o outro, quadril baixo."},
        {"nome": "Caminhada rápida / esteira", "nivel": 1, "so_academia": True, "cronometrado": True,
         "dica": "Postura ereta, braços soltos acompanhando o passo."},
    ],
}

NOME_GRUPO = {
    "peito_ombro_triceps": "Peito, ombro e tríceps",
    "costas_biceps": "Costas e bíceps",
    "pernas": "Pernas e glúteos",
    "core": "Core",
    "cardio_saude": "Cardio e mobilidade",
}


def link_video(nome_exercicio):
    query = urllib.parse.quote(f"{nome_exercicio} como fazer execução correta")
    return f"https://www.youtube.com/results?search_query={query}"


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def buscar_video_youtube(nome_exercicio):
    """Busca o primeiro vídeo relevante via YouTube Data API, se a chave
    estiver configurada nos secrets. Retorna None se não achar ou não tiver
    a chave configurada (nesse caso, cai pro link de busca comum)."""
    if requests is None or "youtube_api_key" not in st.secrets:
        return None
    try:
        resposta = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": f"{nome_exercicio} exercício como fazer",
                "type": "video",
                "maxResults": 1,
                "key": st.secrets["youtube_api_key"],
            },
            timeout=5,
        )
        dados = resposta.json()
        itens = dados.get("items", [])
        if itens:
            return itens[0]["id"]["videoId"]
    except Exception:
        return None
    return None


def niveis_permitidos(nivel_escolhido, idade, motivos):
    nivel_escolhido = int(nivel_escolhido)
    if idade < 18:
        teto_idade = 2
    elif idade <= 60:
        teto_idade = 3
    else:
        teto_idade = 1
    nivel_max = min(nivel_escolhido, teto_idade)
    if "perder_peso" in motivos and nivel_max == 3:
        nivel_max = 2
    return list(range(1, nivel_max + 1))


def nivel_minimo_preferido(niveis_base, sessoes_concluidas):
    """A cada SESSOES_POR_NIVEL treinos concluídos, sobe um degrau de
    preferência dentro do teto permitido pela idade (progressão automática)."""
    degraus = sessoes_concluidas // SESSOES_POR_NIVEL
    teto = max(niveis_base)
    return min(1 + degraus, teto)


def esquema_series(motivos, cronometrado, sessoes_concluidas):
    if "forca" in motivos:
        prioridade = "forca"
    elif "definicao" in motivos:
        prioridade = "definicao"
    elif "verao" in motivos:
        prioridade = "verao"
    else:
        prioridade = "perder_peso"

    bonus = min(sessoes_concluidas // SESSOES_POR_NIVEL, 3)  # progressão automática, até +3 níveis de carga

    if cronometrado:
        esquemas = {
            "forca": (4, 40, "75s"), "definicao": (3, 35, "50s"),
            "verao": (3, 30, "35s"), "perder_peso": (3, 25, "30s"),
        }
        series, segundos, descanso = esquemas[prioridade]
        segundos += bonus * 5
        return series, f"{segundos}s", descanso

    esquemas = {
        "forca": (4, 6, 8, "90s"), "definicao": (4, 10, 12, "60s"),
        "verao": (3, 12, 15, "45s"), "perder_peso": (3, 12, 15, "40s"),
    }
    series, minimo, maximo, descanso = esquemas[prioridade]
    minimo += bonus
    maximo += bonus
    return series, f"{minimo}-{maximo} reps", descanso


def equipamento_disponivel(ex, local, equip, tipo_treino):
    requisito = ex.get("equip_casa")
    if local == "academia" or requisito is None:
        return True
    if tipo_treino == "calistenia" and requisito == "peso":
        return False
    return requisito in equip


def escolher_exercicios(grupo, quantidade, niveis_base, nivel_pref, local, equip, tipo_treino, ja_usados):
    pool = EXERCICIOS[grupo]
    candidatos_pref = [
        ex for ex in pool
        if ex["nivel"] in niveis_base and ex["nivel"] >= nivel_pref
        and (local == "academia" or not ex["so_academia"])
        and equipamento_disponivel(ex, local, equip, tipo_treino)
        and ex["nome"] not in ja_usados
    ]
    candidatos_todos = [
        ex for ex in pool
        if ex["nivel"] in niveis_base
        and (local == "academia" or not ex["so_academia"])
        and equipamento_disponivel(ex, local, equip, tipo_treino)
        and ex["nome"] not in ja_usados
    ]
    fonte = candidatos_pref if len(candidatos_pref) >= quantidade else candidatos_todos
    random.shuffle(fonte)
    escolhidos = fonte[:quantidade]
    for ex in escolhidos:
        ja_usados.add(ex["nome"])
    return escolhidos


def montar_divisao(dias, motivos):
    completo = ["peito_ombro_triceps", "costas_biceps", "pernas", "core"]
    if "perder_peso" in motivos or "verao" in motivos:
        completo.append("cardio_saude")

    if dias <= 3:
        return [completo for _ in range(dias)]
    if dias <= 5:
        padrao = [
            ["peito_ombro_triceps", "costas_biceps", "core"],
            ["pernas", "core", "cardio_saude"],
        ]
        return [padrao[i % 2] for i in range(dias)]
    padrao = [
        ["peito_ombro_triceps", "core"],
        ["costas_biceps", "core"],
        ["pernas", "cardio_saude"],
    ]
    return [padrao[i % 3] for i in range(dias)]


def ajustar_orcamento_por_sexo(grupo, quantidade_base, sexo):
    """Dá uma leve ênfase extra a certos grupos conforme o sexo escolhido,
    sem excluir nenhum exercício — é só uma questão de prioridade."""
    if sexo == "mulher" and grupo == "pernas":
        return quantidade_base + 1
    if sexo == "homem" and grupo in ("peito_ombro_triceps", "costas_biceps"):
        return quantidade_base + 1
    return quantidade_base


def gerar_treino(nivel_escolhido, motivos, local, equip, tipo_treino, sexo, dias, minutos_sessao, idade,
                  sessoes_concluidas):
    niveis_base = niveis_permitidos(nivel_escolhido, idade, motivos)
    nivel_pref = nivel_minimo_preferido(niveis_base, sessoes_concluidas)
    orcamento_exercicios = max(4, min(10, round(minutos_sessao / 7)))
    divisao = montar_divisao(dias, motivos)

    plano = []
    for i, grupos in enumerate(divisao, start=1):
        por_grupo_base = max(1, orcamento_exercicios // len(grupos))
        ja_usados = set()
        blocos = []
        for grupo in grupos:
            por_grupo = ajustar_orcamento_por_sexo(grupo, por_grupo_base, sexo)
            escolhidos = escolher_exercicios(grupo, por_grupo, niveis_base, nivel_pref, local, equip,
                                              tipo_treino, ja_usados)
            lista = []
            for ex in escolhidos:
                cronometrado = ex.get("cronometrado", False)
                series, carga, descanso = esquema_series(motivos, cronometrado, sessoes_concluidas)
                lista.append({
                    "nome": ex["nome"], "nivel": ex["nivel"], "dica": ex["dica"],
                    "series": series, "carga": carga, "descanso": descanso,
                })
            if lista:
                blocos.append({"grupo": grupo, "exercicios": lista})
        plano.append({"dia": f"Dia {i}", "blocos": blocos})
    return plano


def trocar_exercicio(plano, params, dia_idx, bloco_idx, ex_idx):
    """Troca um exercício específico por outro do mesmo grupo, evitando
    repetir exercícios já usados naquele dia. Retorna True se conseguiu
    trocar, False se não achou nenhum substituto disponível."""
    dia = plano[dia_idx]
    bloco = dia["blocos"][bloco_idx]
    grupo = bloco["grupo"]

    niveis_base = niveis_permitidos(params["nivel"], params["idade"], params["motivos"])
    nivel_pref = nivel_minimo_preferido(niveis_base, params["sessoes_concluidas"])
    ja_usados = {ex["nome"] for b in dia["blocos"] for ex in b["exercicios"]}

    novos = escolher_exercicios(
        grupo, 1, niveis_base, nivel_pref, params["local"], params["equip"], params["tipo_treino"], ja_usados,
    )
    if not novos:
        return False

    ex_novo = novos[0]
    cronometrado = ex_novo.get("cronometrado", False)
    series, carga, descanso = esquema_series(params["motivos"], cronometrado, params["sessoes_concluidas"])
    bloco["exercicios"][ex_idx] = {
        "nome": ex_novo["nome"], "nivel": ex_novo["nivel"], "dica": ex_novo["dica"],
        "series": series, "carga": carga, "descanso": descanso,
    }
    return True


def construir_passos_treino(dia):
    """Achata o treino do dia em uma sequência de séries individuais,
    igual ao que o modo treino guiado do forja.html faz."""
    passos = []
    for bloco in dia["blocos"]:
        for ex in bloco["exercicios"]:
            cronometrado = "reps" not in ex["carga"]
            for s in range(1, ex["series"] + 1):
                passos.append({
                    "nome": ex["nome"],
                    "set": s,
                    "totalSets": ex["series"],
                    "work": ex["carga"],
                    "rest": ex["descanso"],
                    "timed": cronometrado,
                })
    return passos


def montar_widget_treino_guiado(passos, dia_label):
    """Gera o mesmo modo treino guiado (cronômetro circular, avanço
    automático entre séries e descanso) usado no forja.html, embutido
    como um componente HTML dentro do Streamlit."""
    dados = json.dumps(passos, ensure_ascii=False)
    dia_label_js = json.dumps(dia_label, ensure_ascii=False)
    return f"""
<meta charset="utf-8">
<div style="font-family:'Inter',sans-serif;background:#12181f;border:1px solid #2c3542;
            border-radius:8px;padding:26px 20px;color:#EDE8DD;">
  <div style="display:flex;justify-content:space-between;font-family:'JetBrains Mono',monospace;
              font-size:12px;color:#a8a396;margin-bottom:18px;">
    <span>{dia_label}</span><span id="woCount"></span>
  </div>
  <div id="woPhase" style="font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:3px;
              color:#4A5560;text-transform:uppercase;text-align:center;margin-bottom:8px;"></div>
  <div id="woExName" style="font-family:'Bebas Neue',sans-serif;font-size:30px;text-align:center;
              margin-bottom:4px;"></div>
  <div id="woSub" style="color:#a8a396;font-size:13px;text-align:center;margin-bottom:26px;"></div>
  <div style="display:flex;justify-content:center;margin-bottom:26px;">
    <div style="position:relative;width:190px;height:190px;">
      <svg width="190" height="190" viewBox="0 0 220 220" style="transform:rotate(-90deg);">
        <circle cx="110" cy="110" r="100" fill="none" stroke="#2c3542" stroke-width="8"></circle>
        <circle id="dialProgress" cx="110" cy="110" r="100" fill="none" stroke="#E8A33D" stroke-width="8"
                stroke-linecap="round" stroke-dasharray="628.3" stroke-dashoffset="0"
                style="transition:stroke-dashoffset .3s linear;"></circle>
      </svg>
      <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;">
        <div id="dialNum" style="font-family:'JetBrains Mono',monospace;font-size:38px;"></div>
        <div id="dialCap" style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#a8a396;"></div>
      </div>
    </div>
  </div>
  <div style="display:flex;gap:10px;justify-content:center;">
    <button id="woSkip" style="padding:12px 22px;border-radius:5px;border:1px solid #4A5560;background:transparent;
                color:#EDE8DD;font-family:'Inter',sans-serif;font-size:13px;cursor:pointer;">Pular</button>
    <button id="woNext" style="padding:12px 26px;border-radius:5px;border:none;background:#E8A33D;
                color:#12181f;font-family:'Bebas Neue',sans-serif;font-size:18px;letter-spacing:1px;
                cursor:pointer;">Concluído</button>
  </div>
</div>
<script>
(function(){{
  const steps = {dados};
  const dayLabel = {dia_label_js};
  let idx = 0, phase = 'exercise', timer = null, timeLeft = 0, total = 0;

  function parseSeconds(str){{ const m = str.match(/(\\d+)/); return m ? parseInt(m[1]) : 30; }}
  function updateDial(left, tot){{
    const circumference = 628.3;
    const frac = tot > 0 ? left / tot : 1;
    document.getElementById('dialProgress').style.strokeDashoffset = circumference * (1 - frac);
    document.getElementById('dialProgress').style.stroke = phase === 'rest' ? '#C1502E' : '#E8A33D';
  }}

  function runStep(){{
    if(idx >= steps.length){{ endWorkout(); return; }}
    const step = steps[idx];
    phase = 'exercise';
    document.getElementById('woCount').textContent = (idx+1) + ' / ' + steps.length;
    document.getElementById('woExName').textContent = step.nome;
    document.getElementById('woSub').textContent = 'Série ' + step.set + ' de ' + step.totalSets;
    document.getElementById('woPhase').textContent = step.timed ? 'execute o tempo' : 'faça a série';
    document.getElementById('dialCap').textContent = 'série';
    document.getElementById('dialNum').textContent = step.set;
    clearInterval(timer);

    if(step.timed){{
      total = parseSeconds(step.work);
      timeLeft = total;
      document.getElementById('dialNum').textContent = timeLeft;
      document.getElementById('dialCap').textContent = 'segundos';
      updateDial(timeLeft, total);
      timer = setInterval(()=>{{
        timeLeft--;
        document.getElementById('dialNum').textContent = timeLeft;
        updateDial(timeLeft, total);
        if(timeLeft<=0){{ clearInterval(timer); startRest(step); }}
      }},1000);
    }} else {{
      updateDial(1,1);
    }}
  }}

  function startRest(step){{
    const isLast = idx === steps.length-1;
    phase = 'rest';
    document.getElementById('woPhase').textContent = 'descanso';
    document.getElementById('woExName').textContent = isLast ? 'Quase lá' : ('Próximo: ' + steps[idx+1].nome);
    document.getElementById('woSub').textContent = 'Respire e prepare a próxima série';
    document.getElementById('dialCap').textContent = 'segundos';
    total = parseSeconds(step.rest);
    timeLeft = total;
    document.getElementById('dialNum').textContent = timeLeft;
    updateDial(timeLeft, total);
    clearInterval(timer);
    timer = setInterval(()=>{{
      timeLeft--;
      document.getElementById('dialNum').textContent = timeLeft;
      updateDial(timeLeft, total);
      if(timeLeft<=0){{ clearInterval(timer); idx++; runStep(); }}
    }},1000);
  }}

  function endWorkout(){{
    clearInterval(timer);
    document.getElementById('woPhase').textContent = 'treino concluído';
    document.getElementById('woExName').textContent = 'Bom trabalho.';
    document.getElementById('woSub').textContent = 'Beba água e alongue por alguns minutos. Marque como concluído abaixo, no Streamlit.';
    document.getElementById('dialNum').textContent = '✓';
    document.getElementById('dialCap').textContent = '';
    updateDial(1,1);
  }}

  document.getElementById('woNext').addEventListener('click', ()=>{{
    clearInterval(timer);
    const step = steps[idx];
    if(phase === 'exercise'){{ startRest(step); }} else {{ idx++; runStep(); }}
  }});
  document.getElementById('woSkip').addEventListener('click', ()=>{{
    clearInterval(timer);
    idx++; runStep();
  }});

  runStep();
}})();
</script>
"""



def montar_pdf_treino(plano, nome_usuario):
    """Gera um PDF com o plano de treino completo, pra baixar e imprimir."""
    import io
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )
    estilos = getSampleStyleSheet()
    titulo_estilo = ParagraphStyle("TituloForja", parent=estilos["Title"], textColor=colors.HexColor("#12181f"))
    subtitulo_estilo = ParagraphStyle("Sub", parent=estilos["Normal"], textColor=colors.HexColor("#6b501f"),
                                       fontSize=10)
    dia_estilo = ParagraphStyle("Dia", parent=estilos["Heading2"], textColor=colors.HexColor("#C1502E"))
    grupo_estilo = ParagraphStyle("Grupo", parent=estilos["Heading4"], textColor=colors.HexColor("#12181f"))
    aviso_estilo = ParagraphStyle("Aviso", parent=estilos["Normal"], fontSize=8, textColor=colors.HexColor("#C1502E"))

    elementos = [
        Paragraph(f"FORJA — Treino de {nome_usuario}", titulo_estilo),
        Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y')}", subtitulo_estilo),
        Spacer(1, 16),
    ]

    for dia in plano:
        elementos.append(Paragraph(dia["dia"], dia_estilo))
        for bloco in dia["blocos"]:
            elementos.append(Paragraph(NOME_GRUPO[bloco["grupo"]], grupo_estilo))
            dados_tabela = [["Exercício", "Séries x carga", "Descanso"]]
            for ex in bloco["exercicios"]:
                dados_tabela.append([ex["nome"], f'{ex["series"]}x {ex["carga"]}', ex["descanso"]])
            tabela = Table(dados_tabela, colWidths=[9 * cm, 5 * cm, 3 * cm])
            tabela.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12181f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            elementos.append(tabela)
            elementos.append(Spacer(1, 10))
        elementos.append(Spacer(1, 14))

    elementos.append(Paragraph(
        "Aviso: este treino é gerado automaticamente e não substitui avaliação médica ou de um "
        "profissional de educação física. Pare imediatamente se sentir dor incomum.",
        aviso_estilo,
    ))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()


def calcular_imc(peso, altura):
    return peso / (altura ** 2)


def classificar_imc(imc):
    if imc < 18.5:
        return "abaixo do peso"
    if imc < 25:
        return "peso adequado"
    if imc < 30:
        return "sobrepeso"
    return "obesidade"


def dicas_dieta(motivos, imc, idade):
    dicas = []
    classe = classificar_imc(imc)

    if "forca" in motivos:
        dicas.append(
            "Para ganhar força, priorize proteína (carnes magras, ovos, feijão, lentilha) em todas as "
            "refeições e não corte demais os carboidratos, eles sustentam a intensidade do treino."
        )
    if "definicao" in motivos:
        dicas.append(
            "Para definição, mantenha a proteína alta e ajuste levemente as calorias para baixo, cortando "
            "açúcar e ultraprocessados, sem exagerar na restrição para não perder massa muscular."
        )
    if "perder_peso" in motivos:
        dicas.append(
            "Para perder peso de forma sustentável, mire um déficit calórico moderado (nada de cortes "
            "drásticos), mantenha a proteína alta pra preservar músculo, e priorize alimentos que saciam "
            "mais: verduras, legumes, proteínas magras e grãos integrais."
        )
    if "verao" in motivos:
        dicas.append(
            "Para o projeto verão, foque na constância mais do que em qualquer dieta radical: boa "
            "hidratação, reduzir sódio e ultraprocessados ajuda a diminuir a retenção de líquido, e "
            "manter a proteína alta preserva a definição que você já tem."
        )

    if classe in ("sobrepeso", "obesidade"):
        dicas.append(
            f"Seu IMC indica {classe}. Um leve déficit calórico ajuda, mas o mais importante é manter a "
            "constância do treino e da alimentação, não a perfeição."
        )
    elif classe == "abaixo do peso":
        dicas.append(
            "Seu IMC indica peso abaixo do recomendado. Vale aumentar levemente as calorias com alimentos "
            "nutritivos em vez de só ultraprocessados."
        )

    if idade > 50:
        dicas.append(
            "Após os 50, a ingestão de cálcio e proteína ganha ainda mais importância para manter ossos e "
            "músculos fortes."
        )

    dicas.append(
        "Estas são orientações gerais, não substituem uma avaliação com nutricionista, especialmente se "
        "você tiver alguma condição de saúde específica."
    )
    return dicas


# ---------------------------------------------------------------------------
# PAINEL DO DONO (acessível via ?admin=1 na URL, protegido por senha)
# ---------------------------------------------------------------------------
if st.query_params.get("admin") == "1":
    st.title("📊 Painel — FORJA")
    senha_admin = st.text_input("Senha de administrador", type="password")
    if senha_admin and senha_admin == st.secrets.get("admin_senha", None):
        usuarios = carregar_usuarios()
        total = len(usuarios)
        ativos = sum(1 for u in usuarios.values() if u.get("assinatura_status") == "ativa")
        em_teste = sum(1 for u in usuarios.values() if u.get("assinatura_status") == "teste")
        cancelados = sum(1 for u in usuarios.values() if u.get("assinatura_status") == "cancelada")
        receita_estimada = ativos * 14.99
        receita_total_recebida = sum(int(u.get("meses_pagos") or 0) for u in usuarios.values()) * 14.99

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Contas totais", total)
        col2.metric("Assinaturas ativas", ativos)
        col3.metric("Em teste grátis", em_teste)
        col4.metric("Canceladas", cancelados)

        col5, col6 = st.columns(2)
        col5.metric("Receita mensal estimada", f"R$ {receita_estimada:.2f}")
        col6.metric("Total já recebido (histórico)", f"R$ {receita_total_recebida:.2f}")

        st.divider()
        hoje = datetime.now().date()
        vencendo = []
        for email, dados in usuarios.items():
            if dados.get("assinatura_status") not in ("ativa", "teste"):
                continue
            try:
                validade = datetime.strptime(str(dados.get("assinatura_valido_ate", "")), "%Y-%m-%d").date()
            except ValueError:
                continue
            dias_restantes = (validade - hoje).days
            if 0 <= dias_restantes <= 3:
                vencendo.append((dados.get("nome", ""), email, dias_restantes))

        if vencendo:
            st.subheader("⏰ Vencendo nos próximos 3 dias")
            for nome, email, dias in sorted(vencendo, key=lambda x: x[2]):
                st.warning(f"**{nome}** ({email}) — vence em {dias} dia(s)")

        st.divider()
        st.subheader("Lista de contas")
        for email, dados in usuarios.items():
            total_pago = int(dados.get("meses_pagos") or 0) * 14.99
            st.write(
                f"**{dados.get('nome','')}** ({email}) — status: `{dados.get('assinatura_status','')}` "
                f"— válido até: {dados.get('assinatura_valido_ate','—')} "
                f"— total pago: R$ {total_pago:.2f}"
            )
    elif senha_admin:
        st.error("Senha incorreta.")
    st.stop()


# ---------------------------------------------------------------------------
# TELA DE ACESSO (login, cadastro e verificação de assinatura)
# ---------------------------------------------------------------------------
LINK_ASSINATURA = "https://pay.cakto.com.br/uga7e39_979154"  # troque pelo link da assinatura mensal na Cakto


def montar_cabecalho(nome=None, emoji_patente=None, nome_patente=None):
    lado_direito = ""
    if nome:
        lado_direito = (
            "<div class='forja-profile'>"
            + (f"<span class='patente-emoji'>{emoji_patente}</span>" if emoji_patente else "")
            + f"<span class='nome'>{nome}</span>"
            + (f"<span class='patente-nome'>· {nome_patente}</span>" if nome_patente else "")
            + "</div>"
        )
    return (
        "<div class='forja-header'>"
        "<div class='forja-brand'><div class='forja-mark'><span>F</span></div>"
        "<h1 style='margin:0;'>FORJA</h1></div>"
        f"{lado_direito}</div>"
    )


if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None
if "reset_email_enviado" not in st.session_state:
    st.session_state["reset_email_enviado"] = None

if st.session_state["usuario_logado"] is None:
    st.markdown(montar_cabecalho(), unsafe_allow_html=True)
    st.write(f"Entre na sua conta FORJA ou crie uma nova — {DIAS_TESTE_GRATIS} dias de teste grátis.")
    aba_entrar, aba_criar, aba_esqueci = st.tabs(["Entrar", "Criar conta", "Esqueci a senha"])

    with aba_entrar:
        with st.form("login_form"):
            email_login = st.text_input("Email", key="email_login")
            senha_login = st.text_input("Senha", type="password", key="senha_login")
            entrar = st.form_submit_button("Entrar")
        if entrar:
            ok, mensagem, usuario = autenticar(email_login, senha_login)
            if ok:
                st.session_state["usuario_logado"] = usuario
                st.rerun()
            else:
                st.error(mensagem)

    with aba_criar:
        with st.form("cadastro_form"):
            nome_cad = st.text_input("Seu nome", key="nome_cad")
            email_cad = st.text_input("Email", key="email_cad")
            senha_cad = st.text_input("Crie uma senha (mín. 6 caracteres)", type="password", key="senha_cad")
            aceite = st.checkbox(
                "Li e aceito os Termos de Uso e a Política de Privacidade, e entendo que devo "
                "consultar um médico antes de iniciar qualquer programa de exercícios.",
                key="aceite_termos",
            )
            criar = st.form_submit_button("Criar conta")
        if criar:
            if not nome_cad.strip() or not email_cad.strip() or len(senha_cad) < 6:
                st.error("Preencha nome, email e uma senha com pelo menos 6 caracteres.")
            elif not aceite:
                st.error("Você precisa aceitar os Termos de Uso e a Política de Privacidade pra continuar.")
            else:
                ok, mensagem = criar_conta(email_cad, senha_cad, nome_cad)
                if ok:
                    st.success(mensagem)
                else:
                    st.error(mensagem)

    with aba_esqueci:
        if st.session_state["reset_email_enviado"] is None:
            with st.form("solicitar_reset_form"):
                email_reset = st.text_input("Email da sua conta", key="email_reset")
                pedir_codigo = st.form_submit_button("Enviar código")
            if pedir_codigo:
                if not email_reset.strip():
                    st.error("Digite seu email.")
                else:
                    ok, mensagem = solicitar_redefinicao_senha(email_reset)
                    st.session_state["reset_email_enviado"] = email_reset.strip().lower() if ok else None
                    st.info(mensagem)
                    if not _email_configurado():
                        st.caption("(envio de email ainda não configurado nos secrets do app)")
        else:
            st.write(f"Digite o código enviado para **{st.session_state['reset_email_enviado']}**.")
            with st.form("redefinir_form"):
                codigo_reset = st.text_input("Código de 6 dígitos", key="codigo_reset")
                nova_senha = st.text_input("Nova senha (mín. 6 caracteres)", type="password", key="nova_senha")
                confirmar_reset = st.form_submit_button("Redefinir senha")
            if confirmar_reset:
                ok, mensagem = redefinir_senha(st.session_state["reset_email_enviado"], codigo_reset, nova_senha)
                if ok:
                    st.success(mensagem)
                    st.session_state["reset_email_enviado"] = None
                else:
                    st.error(mensagem)
            if st.button("Pedir um código novo"):
                st.session_state["reset_email_enviado"] = None
                st.rerun()

    col_pol, col_termos = st.columns(2)
    with col_pol:
        with st.expander("📄 Política de privacidade"):
            st.markdown(TEXTO_POLITICA_PRIVACIDADE)
    with col_termos:
        with st.expander("📄 Termos de uso"):
            st.markdown(TEXTO_TERMOS_DE_USO)
    st.stop()

usuario_logado = st.session_state["usuario_logado"]
status = status_acesso(usuario_logado)

_historico_cabecalho = carregar_historico()
_perfil_cabecalho = obter_perfil(_historico_cabecalho, usuario_logado["email"])
(_, _nome_patente, _emoji_patente, _), _ = calcular_patente(len(_perfil_cabecalho.get("datas_treinos", [])))
st.markdown(
    montar_cabecalho(usuario_logado.get("nome", ""), _emoji_patente, _nome_patente),
    unsafe_allow_html=True,
)

if not status["liberado"]:
    st.write(f"Olá, {usuario_logado.get('nome', '')}!")
    if status["motivo"] == "expirado":
        st.write(f"Seu período de acesso acabou. Assine por **{PRECO_MENSAL}/mês** pra continuar.")
    else:
        st.write(f"Sua assinatura não está ativa ainda. Assine por **{PRECO_MENSAL}/mês** pra liberar o acesso.")
    st.link_button(f"Assinar agora — {PRECO_MENSAL}/mês ↗", LINK_ASSINATURA)
    st.caption(f"Use este mesmo email no checkout ({usuario_logado['email']}), pra liberação automática.")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Já assinei, verificar de novo"):
            recarregar_usuario_logado()
            st.rerun()
    with col_b:
        if st.button("Sair da conta"):
            st.session_state["usuario_logado"] = None
            st.rerun()
    st.stop()

if status["em_tolerancia"]:
    rotulo_periodo = "teste grátis" if status["motivo"] == "teste" else "assinatura"
    st.warning(
        f"Seu(a) {rotulo_periodo} venceu, mas você ainda tem {status['dias_restantes']} dia(s) de tolerância. "
        f"Assine pra não perder o acesso."
    )
    st.link_button(f"Assinar agora — {PRECO_MENSAL}/mês ↗", LINK_ASSINATURA)
elif status["motivo"] == "teste":
    col_info, col_btn = st.columns([2, 1])
    with col_info:
        st.info(f"Você está no teste grátis — {status['dias_restantes']} dia(s) restante(s).")
    with col_btn:
        st.link_button(f"Assinar agora — {PRECO_MENSAL}/mês ↗", LINK_ASSINATURA)

with st.expander(f"👤 {usuario_logado.get('nome','')}"):
    if status["motivo"] == "teste":
        st.write(f"Teste grátis válido até {usuario_logado.get('assinatura_valido_ate','')}.")
    else:
        st.write(f"Assinatura válida até {usuario_logado.get('assinatura_valido_ate','')}.")
    if st.button("Sair da conta", key="sair_logado"):
        st.session_state["usuario_logado"] = None
        st.rerun()

def escolha_unica(chave, opcoes, cols):
    """Renderiza um grid de botões de escolha única (estilo card) e
    devolve o valor selecionado, guardando em st.session_state[chave]."""
    if chave not in st.session_state:
        st.session_state[chave] = None
    linhas = [opcoes[i:i + cols] for i in range(0, len(opcoes), cols)]
    for linha in linhas:
        colunas = st.columns(len(linha))
        for coluna, (valor, titulo, subtitulo) in zip(colunas, linha):
            with coluna:
                selecionado = st.session_state[chave] == valor
                if st.button(titulo, key=f"{chave}_{valor}", use_container_width=True,
                             type="primary" if selecionado else "secondary"):
                    st.session_state[chave] = valor
                    st.rerun()
                if subtitulo:
                    st.caption(subtitulo)
    return st.session_state[chave]


def escolha_multipla(chave, opcoes, cols):
    """Igual à escolha_unica, mas permite marcar mais de uma opção."""
    if chave not in st.session_state:
        st.session_state[chave] = set()
    linhas = [opcoes[i:i + cols] for i in range(0, len(opcoes), cols)]
    for linha in linhas:
        colunas = st.columns(len(linha))
        for coluna, (valor, titulo, subtitulo) in zip(colunas, linha):
            with coluna:
                selecionado = valor in st.session_state[chave]
                if st.button(titulo, key=f"{chave}_{valor}", use_container_width=True,
                             type="primary" if selecionado else "secondary"):
                    if selecionado:
                        st.session_state[chave].discard(valor)
                    else:
                        st.session_state[chave].add(valor)
                    st.rerun()
                if subtitulo:
                    st.caption(subtitulo)
    return st.session_state[chave]


# ---------------------------------------------------------------------------
# INTERFACE
# ---------------------------------------------------------------------------
with st.expander("📸 Feed da comunidade — veja e compartilhe sua evolução"):
    historico_feed = carregar_historico()
    perfil_feed = obter_perfil(historico_feed, usuario_logado["email"])
    streak_feed, _ = calcular_streak(perfil_feed.get("datas_treinos", []))

    with st.form("post_feed_form", clear_on_submit=True):
        texto_post = st.text_area("Compartilhe algo sobre seu treino hoje", max_chars=280, key="texto_post")
        publicar = st.form_submit_button("Publicar")
    if publicar:
        if publicar_no_feed(usuario_logado["email"], usuario_logado.get("nome", ""), texto_post, streak_feed):
            st.success("Publicado!")
            st.rerun()
        else:
            st.error("Escreva algo antes de publicar.")

    st.divider()
    posts = carregar_feed()
    if not posts:
        st.caption("Ainda não tem nenhuma publicação. Seja a primeira pessoa a compartilhar!")
    for post in posts[:30]:
        curtidas = post.get("curtidas", [])
        ja_curtiu = usuario_logado["email"] in curtidas
        st.markdown(
            f"<div class='ex-card'><div class='ex-top'>"
            f"<span class='ex-nome'>{post['nome']}</span>"
            f"<span class='ex-scheme'>🔥 {post.get('streak','0')} dia(s)</span>"
            f"</div><div class='ex-dica' style='margin-top:6px;'>{post['texto']}</div>"
            f"<div class='ex-dica' style='margin-top:6px;color:#4A5560;'>{post['data']}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        col_like, _ = st.columns([1, 5])
        with col_like:
            rotulo = f"❤ {len(curtidas)}" if not ja_curtiu else f"💔 {len(curtidas)}"
            if st.button(rotulo, key=f"like_{post['id']}"):
                curtir_post(post["id"], usuario_logado["email"])
                st.rerun()

st.write("Preencha seus dados e receba um plano de treino semanal que evolui sozinho a cada treino concluído.")

with st.container(border=True):
    st.markdown("<div class='onb-eyebrow'>00 — DADOS PESSOAIS</div>", unsafe_allow_html=True)
    nome = usuario_logado.get("nome", "")
    st.write(f"Treinando como **{nome}**")
    col1, col2 = st.columns(2)
    with col1:
        peso = st.number_input("Peso (kg)", min_value=30.0, max_value=250.0, value=70.0, step=0.5)
        idade = st.number_input("Idade", min_value=12, max_value=90, value=25, step=1)
    with col2:
        altura = st.number_input("Altura (m)", min_value=1.20, max_value=2.20, value=1.70, step=0.01)

with st.container(border=True):
    st.markdown("<div class='onb-eyebrow'>01 — SEXO</div>", unsafe_allow_html=True)
    sexo = escolha_unica("onb_sexo", [
        ("homem", "Homem", None),
        ("mulher", "Mulher", None),
    ], cols=2)

with st.container(border=True):
    st.markdown("<div class='onb-eyebrow'>02 — NÍVEL</div>", unsafe_allow_html=True)
    nivel = escolha_unica("onb_nivel", [
        ("1", "Iniciante", "pouco ou nenhum treino"),
        ("2", "Intermediário", "treina há alguns meses"),
        ("3", "Avançado", "já domina o peso do corpo"),
    ], cols=3)

with st.container(border=True):
    st.markdown("<div class='onb-eyebrow'>03 — OBJETIVO</div>", unsafe_allow_html=True)
    objetivos = escolha_multipla("onb_objetivos", [
        ("forca", "Força", "poucas reps, mais carga"),
        ("definicao", "Definição", "volume moderado"),
        ("perder_peso", "Perder peso", "circuito, mais cardio"),
        ("verao", "Projeto verão", "corpo todo, foco em constância"),
    ], cols=4)

with st.container(border=True):
    st.markdown("<div class='onb-eyebrow'>04 — ROTINA</div>", unsafe_allow_html=True)
    st.markdown("<div class='onb-sublabel'>Dias de treino por semana</div>", unsafe_allow_html=True)
    dias = escolha_unica("onb_dias", [
        ("2", "2 dias", None), ("3", "3 dias", None), ("4", "4 dias", None), ("5", "5 dias", None),
        ("6", "6 dias", None),
    ], cols=4)
    st.markdown("<div class='onb-sublabel'>Tempo disponível por sessão</div>", unsafe_allow_html=True)
    minutos_sessao = escolha_unica("onb_minutos", [
        ("20", "20 min", None), ("35", "35 min", None), ("50", "50 min", None), ("70", "70 min", None),
    ], cols=4)

with st.container(border=True):
    st.markdown("<div class='onb-eyebrow'>05 — TIPO DE TREINO</div>", unsafe_allow_html=True)
    tipo_treino = escolha_unica("onb_tipo_treino", [
        ("calistenia", "Calistenia", "só o peso do corpo, sem peso extra"),
        ("treino_casa", "Treino em casa", "libera halteres/peso livre também"),
    ], cols=2)

with st.container(border=True):
    st.markdown("<div class='onb-eyebrow'>06 — EQUIPAMENTO EM CASA</div>", unsafe_allow_html=True)
    st.markdown("<div class='onb-sublabel'>Marque tudo que você tem (cadeira/parede sempre contam)</div>", unsafe_allow_html=True)
    equip = escolha_multipla("onb_equip", [
        ("bar", "Barra fixa", None),
        ("band", "Elástico / faixa", None),
        ("peso", "Halteres / peso livre", None),
        ("none", "Só o corpo mesmo", None),
    ], cols=4)

with st.container(border=True):
    st.markdown("<div class='onb-eyebrow'>07 — LOCAL DE TREINO</div>", unsafe_allow_html=True)
    local_valor = escolha_unica("onb_local", [
        ("casa", "Casa", None),
        ("academia", "Academia", None),
    ], cols=2)

st.write("")
enviado = st.button("Gerar meu treino", type="primary", use_container_width=True)

if enviado:
    if not sexo:
        st.error("Escolha uma opção em sexo.")
    elif not st.session_state["onb_nivel"]:
        st.error("Escolha seu nível.")
    elif not objetivos:
        st.error("Escolha ao menos um objetivo para o treino.")
    elif not st.session_state["onb_dias"] or not st.session_state["onb_minutos"]:
        st.error("Escolha os dias por semana e o tempo por sessão.")
    elif not tipo_treino:
        st.error("Escolha o tipo de treino.")
    elif not local_valor:
        st.error("Escolha o local de treino.")
    else:
        historico = carregar_historico()
        perfil = obter_perfil(historico, usuario_logado["email"])
        imc = calcular_imc(peso, altura)
        motivos_opcoes = list(objetivos)
        plano = gerar_treino(
            nivel, motivos_opcoes, local_valor, equip, tipo_treino, sexo, int(dias), int(minutos_sessao),
            int(idade), perfil["sessoes_concluidas"],
        )

        st.session_state["plano"] = plano
        st.session_state["imc"] = imc
        st.session_state["motivos"] = motivos_opcoes
        st.session_state["idade"] = idade
        st.session_state["nome"] = nome
        st.session_state["perfil"] = perfil
        st.session_state["ver_treino_mesmo_assim"] = False
        st.session_state["parametros_geracao"] = {
            "nivel": nivel, "motivos": motivos_opcoes, "local": local_valor, "equip": equip,
            "tipo_treino": tipo_treino, "idade": int(idade), "sessoes_concluidas": perfil["sessoes_concluidas"],
        }

if "plano" in st.session_state:
    plano = st.session_state["plano"]
    imc = st.session_state["imc"]
    motivos_opcoes = st.session_state["motivos"]
    idade = st.session_state["idade"]
    nome_atual = usuario_logado["email"]
    perfil = st.session_state["perfil"]

    st.divider()

    sessoes = perfil["sessoes_concluidas"]
    faltam = SESSOES_POR_NIVEL - (sessoes % SESSOES_POR_NIVEL)
    st.markdown(
        f"<span class='pill'>IMC {imc:.1f} · {classificar_imc(imc)}</span>"
        f"<span class='pill'>{sessoes} treinos concluídos</span>"
        f"<span class='pill'>faltam {faltam} para subir de nível</span>",
        unsafe_allow_html=True,
    )
    st.progress((sessoes % SESSOES_POR_NIVEL) / SESSOES_POR_NIVEL)

    streak_atual, melhor_streak = calcular_streak(perfil.get("datas_treinos", []))
    st.markdown(
        f"<span class='pill'>🔥 sequência atual: {streak_atual} dia(s)</span>"
        f"<span class='pill'>🏆 melhor sequência: {melhor_streak} dia(s)</span>",
        unsafe_allow_html=True,
    )
    st.markdown(montar_heatmap_treinos(perfil.get("datas_treinos", [])), unsafe_allow_html=True)
    st.markdown(montar_cartao_patente(len(perfil.get("datas_treinos", []))), unsafe_allow_html=True)

    conquistas = calcular_conquistas(perfil)
    if conquistas:
        st.markdown(
            "".join(f"<span class='pill'>{emoji} {titulo}</span>" for emoji, titulo in conquistas),
            unsafe_allow_html=True,
        )

    (_, _nome_patente_card, _, _), _ = calcular_patente(len(perfil.get("datas_treinos", [])))
    _streak_atual_card, _melhor_streak_card = calcular_streak(perfil.get("datas_treinos", []))
    imagem_patente = montar_imagem_patente(
        usuario_logado.get("nome", ""), _nome_patente_card, _streak_atual_card, _melhor_streak_card,
        len(perfil.get("datas_treinos", [])), perfil.get("sessoes_concluidas", 0),
    )
    st.download_button(
        "📸 Baixar card pra compartilhar",
        data=imagem_patente,
        file_name="forja_patente.png",
        mime="image/png",
    )

    hoje_str = datetime.now().strftime("%Y-%m-%d")
    ja_treinou_hoje = hoje_str in perfil.get("datas_treinos", [])
    if "ver_treino_mesmo_assim" not in st.session_state:
        st.session_state["ver_treino_mesmo_assim"] = False

    if ja_treinou_hoje and not st.session_state["ver_treino_mesmo_assim"]:
        st.divider()
        st.markdown(
            "<div style='text-align:center;padding:30px 10px;'>"
            "<div style='font-family:\"Bebas Neue\",sans-serif;font-size:34px;color:#E8A33D;'>"
            "✓ Treino de hoje concluído!</div>"
            "<div style='color:#a8a396;font-size:14px;margin-top:8px;'>"
            "Bom trabalho. Descanse e volte amanhã pro próximo treino.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        if st.button("Ver o treino de hoje mesmo assim"):
            st.session_state["ver_treino_mesmo_assim"] = True
            st.rerun()
    else:
        st.subheader("Seu plano semanal")
        pdf_bytes = montar_pdf_treino(plano, usuario_logado.get("nome", ""))
        st.download_button(
            "📄 Baixar treino em PDF",
            data=pdf_bytes,
            file_name="forja_treino.pdf",
            mime="application/pdf",
        )
        if "modo_treino_dia" not in st.session_state:
            st.session_state["modo_treino_dia"] = None

        abas = st.tabs([dia["dia"] for dia in plano])
        for dia_idx, (aba, dia) in enumerate(zip(abas, plano)):
            with aba:
                for bloco_idx, bloco in enumerate(dia["blocos"]):
                    st.markdown(f"<div class='grp-label'>{NOME_GRUPO[bloco['grupo']]}</div>", unsafe_allow_html=True)
                    for ex_idx, ex in enumerate(bloco["exercicios"]):
                        st.markdown(f"""
                            <div class="ex-card">
                              <div class="ex-top">
                                <span class="ex-nome">{ex['nome']}<span class="ex-nivel">{'●' * ex['nivel']}</span></span>
                                <span class="ex-scheme">{ex['series']}x {ex['carga']} · descanso {ex['descanso']}</span>
                              </div>
                              <div class="ex-dica">{ex['dica']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        video_id = buscar_video_youtube(ex["nome"])
                        if video_id:
                            with st.expander(f"▶ Ver demonstração — {ex['nome']}"):
                                st.video(f"https://www.youtube.com/watch?v={video_id}")
                        else:
                            st.markdown(
                                f"<a class='ex-link' href='{link_video(ex['nome'])}' target='_blank'>"
                                f"Ver demonstração ↗</a>",
                                unsafe_allow_html=True,
                            )
                        if st.button("🔄 Trocar esse exercício", key=f"trocar_{dia_idx}_{bloco_idx}_{ex_idx}"):
                            sucesso = trocar_exercicio(
                                st.session_state["plano"], st.session_state["parametros_geracao"],
                                dia_idx, bloco_idx, ex_idx,
                            )
                            if sucesso:
                                st.rerun()
                            else:
                                st.warning("Não achei outro exercício disponível pra esse grupo agora.")

                if st.session_state["modo_treino_dia"] == dia["dia"]:
                    passos = construir_passos_treino(dia)
                    components.html(montar_widget_treino_guiado(passos, dia["dia"]), height=560, scrolling=False)
                    if st.button("Sair do modo guiado", key=f"sair_{dia['dia']}"):
                        st.session_state["modo_treino_dia"] = None
                        st.rerun()
                else:
                    if st.button(f"▶ Iniciar treino guiado — {dia['dia']}", key=f"iniciar_{dia['dia']}"):
                        st.session_state["modo_treino_dia"] = dia["dia"]
                        st.rerun()

        st.divider()
        if st.button("✓ Concluí o treino de hoje"):
            novo_perfil = registrar_sessao_concluida(nome_atual)
            st.session_state["perfil"] = novo_perfil
            st.session_state["ver_treino_mesmo_assim"] = False
            st.success(f"Treino registrado! Total: {novo_perfil['sessoes_concluidas']} treinos concluídos.")
            st.rerun()

    st.divider()
    st.subheader("Dicas de dieta")
    for dica in dicas_dieta(motivos_opcoes, imc, idade):
        st.write(f"- {dica}")

    st.divider()
    st.caption(
        "⚠️ Este treino é gerado automaticamente e não substitui avaliação médica ou de um "
        "profissional de educação física. Pare imediatamente se sentir dor incomum."
    )
