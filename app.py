import json
import os
import random
import urllib.parse
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Treino de Calistenia", page_icon="💪", layout="centered")

HISTORICO_ARQUIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historico_treino.json")
SESSOES_POR_NIVEL = 4  # a cada N treinos concluídos, o app sobe um degrau de dificuldade

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

.forja-header { display:flex; align-items:center; gap:14px; margin-bottom:2px; }
.forja-mark { width:38px; height:38px; flex:none; border:2px solid #E8A33D; display:flex; align-items:center;
  justify-content:center; font-family:'Bebas Neue',sans-serif; font-size:18px; color:#E8A33D; transform:rotate(45deg); }
.forja-mark span { transform:rotate(-45deg); display:block; }

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

st.markdown(
    "<div class='forja-header'><div class='forja-mark'><span>F</span></div><h1 style='margin:0;'>FORJA</h1></div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# PERSISTÊNCIA (progressão automática entre sessões)
# ---------------------------------------------------------------------------
def carregar_historico():
    if os.path.exists(HISTORICO_ARQUIVO):
        try:
            with open(HISTORICO_ARQUIVO, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def salvar_historico(historico):
    with open(HISTORICO_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)


def obter_perfil(historico, nome):
    return historico.get(nome, {"sessoes_concluidas": 0, "ultimo_treino": None})


def registrar_sessao_concluida(nome):
    historico = carregar_historico()
    perfil = obter_perfil(historico, nome)
    perfil["sessoes_concluidas"] += 1
    perfil["ultimo_treino"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    historico[nome] = perfil
    salvar_historico(historico)
    return perfil


# ---------------------------------------------------------------------------
# ACESSO PAGO (código liberado após a compra no Stripe)
# ---------------------------------------------------------------------------
CODIGOS_ARQUIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "codigos_acesso.json")


def carregar_codigos():
    if os.path.exists(CODIGOS_ARQUIVO):
        try:
            with open(CODIGOS_ARQUIVO, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def salvar_codigos(codigos):
    with open(CODIGOS_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(codigos, f, ensure_ascii=False, indent=2)


def validar_codigo(codigo, nome_comprador):
    """Retorna (True, mensagem) se o código existe e pode ser usado por essa
    pessoa. Uma vez que um código é vinculado a um nome, a mesma pessoa pode
    reenviar o mesmo código (ex: pelo link salvo) sem ser bloqueada; só uma
    pessoa diferente tentando o mesmo código é que é recusada."""
    codigo = codigo.strip().upper()
    nome_comprador = nome_comprador.strip()
    codigos = carregar_codigos()
    if codigo not in codigos:
        return False, "Código não encontrado. Confira se digitou certo."
    registro = codigos[codigo]
    if registro.get("usado") and registro.get("usado_por") != nome_comprador:
        return False, "Esse código já foi usado em outro acesso."
    if not registro.get("usado"):
        registro["usado"] = True
        registro["usado_por"] = nome_comprador
        registro["data_uso"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        salvar_codigos(codigos)
    return True, "Acesso liberado!"


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
# TELA DE ACESSO (paga)
# ---------------------------------------------------------------------------
if "acesso_liberado" not in st.session_state:
    st.session_state["acesso_liberado"] = False

# Tenta liberar automaticamente se o código já estiver salvo na URL
# (isso acontece quando a pessoa acessa por um link que ela salvou/favoritou
# depois da primeira liberação).
if not st.session_state["acesso_liberado"]:
    codigo_url = st.query_params.get("codigo")
    nome_url = st.query_params.get("nome")
    if codigo_url and nome_url:
        valido, _ = validar_codigo(codigo_url, nome_url)
        if valido:
            st.session_state["acesso_liberado"] = True

if not st.session_state["acesso_liberado"]:
    st.write("Acesso ao FORJA: R$ 7,99. Pague pelo link abaixo e você recebe um código de acesso.")
    st.link_button("Pagar R$ 7,99 e gerar meu acesso ↗", "https://pay.cakto.com.br/uga7e39_979154")
    st.write("")
    with st.form("codigo_form"):
        codigo_digitado = st.text_input("Já tem um código de acesso? Digite aqui")
        nome_comprador = st.text_input("Seu nome")
        confirmar = st.form_submit_button("Liberar acesso")
    if confirmar:
        if not codigo_digitado.strip() or not nome_comprador.strip():
            st.error("Preencha o código e o seu nome.")
        else:
            valido, mensagem = validar_codigo(codigo_digitado, nome_comprador.strip())
            if valido:
                st.session_state["acesso_liberado"] = True
                # guarda o código na URL para não precisar digitar de novo depois
                st.query_params["codigo"] = codigo_digitado.strip().upper()
                st.query_params["nome"] = nome_comprador.strip()
                st.success(mensagem)
                st.rerun()
            else:
                st.error(mensagem)
    st.stop()
else:
    with st.expander("💾 Não perca seu acesso"):
        st.write(
            "Adicione esta página aos favoritos do seu navegador agora. "
            "Da próxima vez que abrir por esse favorito, o acesso libera "
            "sozinho, sem precisar digitar o código de novo."
        )

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
st.write("Preencha seus dados e receba um plano de treino semanal que evolui sozinho a cada treino concluído.")

with st.container(border=True):
    st.markdown("<div class='onb-eyebrow'>00 — DADOS PESSOAIS</div>", unsafe_allow_html=True)
    nome = st.text_input("Seu nome (usado para salvar seu progresso)", value=st.session_state.get("onb_nome", "Você"))
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
    elif not nome.strip():
        st.error("Digite um nome para salvarmos seu progresso.")
    else:
        historico = carregar_historico()
        perfil = obter_perfil(historico, nome.strip())
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
        st.session_state["nome"] = nome.strip()
        st.session_state["perfil"] = perfil

if "plano" in st.session_state:
    plano = st.session_state["plano"]
    imc = st.session_state["imc"]
    motivos_opcoes = st.session_state["motivos"]
    idade = st.session_state["idade"]
    nome_atual = st.session_state["nome"]
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

    st.subheader("Seu plano semanal")
    if "modo_treino_dia" not in st.session_state:
        st.session_state["modo_treino_dia"] = None

    abas = st.tabs([dia["dia"] for dia in plano])
    for aba, dia in zip(abas, plano):
        with aba:
            for bloco in dia["blocos"]:
                st.markdown(f"<div class='grp-label'>{NOME_GRUPO[bloco['grupo']]}</div>", unsafe_allow_html=True)
                for ex in bloco["exercicios"]:
                    video = link_video(ex["nome"])
                    st.markdown(f"""
                        <div class="ex-card">
                          <div class="ex-top">
                            <span class="ex-nome">{ex['nome']}<span class="ex-nivel">{'●' * ex['nivel']}</span></span>
                            <span class="ex-scheme">{ex['series']}x {ex['carga']} · descanso {ex['descanso']}</span>
                          </div>
                          <div class="ex-dica">{ex['dica']}</div>
                          <a class="ex-link" href="{video}" target="_blank">Ver demonstração ↗</a>
                        </div>
                        """, unsafe_allow_html=True)

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
        st.success(f"Treino registrado! Total: {novo_perfil['sessoes_concluidas']} treinos concluídos.")
        st.rerun()

    st.divider()
    st.subheader("Dicas de dieta")
    for dica in dicas_dieta(motivos_opcoes, imc, idade):
        st.write(f"- {dica}")
