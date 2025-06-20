from flask import Blueprint, jsonify, request, render_template, url_for, session
import modules.delgrande.relatorios.utils as utils
from application.models import db, DesempenhoAtendente, DesempenhoAtendenteVyrtos
from modules.delgrande.auth.utils import authenticate, authenticate_relatorio
from application.models import Chamado
from settings.endpoints import CREDENTIALS
from datetime import datetime, timedelta
from sqlalchemy import func, cast, Date

operadores_bp = Blueprint('operadores_bp', __name__, url_prefix='/operadores')


@operadores_bp.route('/performanceColaboradores', methods=['POST'])
def get_performance_colaboradores():
    OPERADORES_IDS = {
        "Matheus": 2021,
        "Renato": 2020,
        "Gustavo": 2022,
        "Raysa": 2023,
        "Danilo": 2025
    }

    data = request.get_json()
    nome = data.get('nome')
    dias_str = data.get('dias', '1')  # Recebe string, ex: '7', '15'

    if not nome:
        return jsonify({"status": "error", "message": "Nome do operador não fornecido"}), 400

    operador_id = OPERADORES_IDS.get(nome)
    if not operador_id:
        return jsonify({"status": "error", "message": f"Operador '{nome}' não encontrado"}), 404

    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    if "access_token" not in auth_response:
        return jsonify({"status": "error", "message": "Falha na autenticação"}), 401

    access_token = auth_response["access_token"]

    hoje = datetime.now()
    ontem = hoje - timedelta(days=1)

    # Dicionário que mapeia o número de dias para a data inicial (string)
    periodos = {
        "1": (ontem).strftime('%Y-%m-%d'),  # Ontem
        "7": (ontem - timedelta(days=6)).strftime('%Y-%m-%d'),  # De 6 dias atrás até ontem
        "15": (ontem - timedelta(days=14)).strftime('%Y-%m-%d'),
        "30": (ontem - timedelta(days=29)).strftime('%Y-%m-%d'),
        "90": (ontem - timedelta(days=89)).strftime('%Y-%m-%d')
    }

    # Pega a data inicial conforme o parâmetro dias, se inválido usa '1'
    data_inicial = periodos.get(dias_str, periodos["1"])
    data_final = (hoje - timedelta(days=1)).strftime('%Y-%m-%d')

    class Params:
        initial_date = data_inicial
        final_date = data_final
        initial_hour = "00:00:00"
        final_hour = "23:59:59"
        week = ""
        agents = [operador_id]
        queues = [1]
        options = {
            "sort": {"data": -1},
            "offset": 0,
            "count": 1000
        }
        conf = {}

    response = utils.atendentePerformance(access_token, Params)
    dados_atendentes = response.get("result", {}).get("data", [])

    if not dados_atendentes:
        return jsonify({"status": "error", "message": "Nenhum dado encontrado para esse colaborador"}), 404

    # Acumula os dados no período
    acumulado = {
        "ch_atendidas": 0,
        "ch_naoatendidas": 0,
        "tempo_online": 0,
        "tempo_livre": 0,
        "tempo_servico": 0,
        "pimprod_Refeicao": 0,
        "tempo_minatend": None,
        "tempo_medatend": [],
        "tempo_maxatend": None
    }

    for item in dados_atendentes:
        acumulado["ch_atendidas"] += item.get("ch_atendidas", 0)
        acumulado["ch_naoatendidas"] += item.get("ch_naoatendidas", 0)
        acumulado["tempo_online"] += item.get("tempo_online", 0)
        acumulado["tempo_livre"] += item.get("tempo_livre", 0)
        acumulado["tempo_servico"] += item.get("tempo_servico", 0)
        acumulado["pimprod_Refeicao"] += item.get("pimprod_Refeicao", 0)

        if item.get("tempo_minatend") is not None:
            if acumulado["tempo_minatend"] is None or item["tempo_minatend"] < acumulado["tempo_minatend"]:
                acumulado["tempo_minatend"] = item["tempo_minatend"]

        if item.get("tempo_maxatend") is not None:
            if acumulado["tempo_maxatend"] is None or item["tempo_maxatend"] > acumulado["tempo_maxatend"]:
                acumulado["tempo_maxatend"] = item["tempo_maxatend"]

        if item.get("tempo_medatend") is not None:
            acumulado["tempo_medatend"].append(item["tempo_medatend"])

    media_geral = (
        sum(acumulado["tempo_medatend"]) / len(acumulado["tempo_medatend"])
        if acumulado["tempo_medatend"] else 0
    )

    dados = {
        "ch_atendidas": acumulado["ch_atendidas"],
        "ch_naoatendidas": acumulado["ch_naoatendidas"],
        "tempo_online": acumulado["tempo_online"],
        "tempo_livre": acumulado["tempo_livre"],
        "tempo_servico": acumulado["tempo_servico"],
        "pimprod_Refeicao": acumulado["pimprod_Refeicao"],
        "tempo_minatend": acumulado["tempo_minatend"] or 0,
        "tempo_medatend": round(media_geral, 2),
        "tempo_maxatend": acumulado["tempo_maxatend"] or 0
    }

    session['nome'] = nome
    session['dados'] = dados

    return jsonify({"redirect_url": url_for('operadores_bp.render_operadores')})


@operadores_bp.route('/colaboradores', methods=['GET'])
def render_operadores():
    nome = session.get('nome')
    dados = session.get('dados')
    total_chamados = session.get('total_chamados', 0)  # Pega da sessão, default 0

    if not nome or not dados:
        return "Dados não encontrados na sessão", 400

    return render_template('colaboradores.html', nome=nome, dados=dados, total_chamados=total_chamados)

'''@operadores_bp.route('/performanceColaboradoresUpdate', methods=['POST'])
def get_performance_colaboradores_update():
    OPERADORES_IDS = {
        "Matheus": 2021,
        "Renato": 2020,
        "Gustavo": 2022,
        "Raysa": 2023,
        "Danilo": 2025
    }

    data = request.get_json()
    nome = data.get('nome')
    dias_str = data.get('dias', '1')  # Recebe string, ex: '7', '15'

    if not nome:
        return jsonify({"status": "error", "message": "Nome do operador não fornecido"}), 400

    operador_id = OPERADORES_IDS.get(nome)
    if not operador_id:
        return jsonify({"status": "error", "message": f"Operador '{nome}' não encontrado"}), 404

    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    if "access_token" not in auth_response:
        return jsonify({"status": "error", "message": "Falha na autenticação"}), 401

    access_token = auth_response["access_token"]

    hoje = datetime.now()
    ontem = hoje - timedelta(days=1)

    # Dicionário que mapeia o número de dias para a data inicial (string)
    periodos = {
        "1": (ontem).strftime('%Y-%m-%d'),  # Ontem
        "7": (ontem - timedelta(days=6)).strftime('%Y-%m-%d'),  # De 6 dias atrás até ontem
        "15": (ontem - timedelta(days=14)).strftime('%Y-%m-%d'),
        "30": (ontem - timedelta(days=29)).strftime('%Y-%m-%d'),
        "90": (ontem - timedelta(days=89)).strftime('%Y-%m-%d')
    }

    # Pega a data inicial conforme o parâmetro dias, se inválido usa '1'
    data_inicial = periodos.get(dias_str, periodos["1"])
    data_final = (hoje - timedelta(days=1)).strftime('%Y-%m-%d')

    class Params:
        initial_date = data_inicial
        final_date = data_final
        initial_hour = "00:00:00"
        final_hour = "23:59:59"
        week = ""
        agents = [operador_id]
        queues = [1]
        options = {
            "sort": {"data": -1},
            "offset": 0,
            "count": 1000
        }
        conf = {}

    response = utils.atendentePerformance(access_token, Params)
    dados_atendentes = response.get("result", {}).get("data", [])

    if not dados_atendentes:
        return jsonify({"status": "error", "message": "Nenhum dado encontrado para esse colaborador"}), 404

    # Acumula os dados no período
    acumulado = {
        "ch_atendidas": 0,
        "ch_naoatendidas": 0,
        "tempo_online": 0,
        "tempo_livre": 0,
        "tempo_servico": 0,
        "pimprod_Refeicao": 0,
        "tempo_minatend": None,
        "tempo_medatend": [],
        "tempo_maxatend": None
    }

    for item in dados_atendentes:
        acumulado["ch_atendidas"] += item.get("ch_atendidas", 0)
        acumulado["ch_naoatendidas"] += item.get("ch_naoatendidas", 0)
        acumulado["tempo_online"] += item.get("tempo_online", 0)
        acumulado["tempo_livre"] += item.get("tempo_livre", 0)
        acumulado["tempo_servico"] += item.get("tempo_servico", 0)
        acumulado["pimprod_Refeicao"] += item.get("pimprod_Refeicao", 0)

        if item.get("tempo_minatend") is not None:
            if acumulado["tempo_minatend"] is None or item["tempo_minatend"] < acumulado["tempo_minatend"]:
                acumulado["tempo_minatend"] = item["tempo_minatend"]

        if item.get("tempo_maxatend") is not None:
            if acumulado["tempo_maxatend"] is None or item["tempo_maxatend"] > acumulado["tempo_maxatend"]:
                acumulado["tempo_maxatend"] = item["tempo_maxatend"]

        if item.get("tempo_medatend") is not None:
            acumulado["tempo_medatend"].append(item["tempo_medatend"])

    media_geral = (
        sum(acumulado["tempo_medatend"]) / len(acumulado["tempo_medatend"])
        if acumulado["tempo_medatend"] else 0
    )

    dados = {
        "ch_atendidas": acumulado["ch_atendidas"],
        "ch_naoatendidas": acumulado["ch_naoatendidas"],
        "tempo_online": acumulado["tempo_online"],
        "tempo_livre": acumulado["tempo_livre"],
        "tempo_servico": acumulado["tempo_servico"],
        "pimprod_Refeicao": acumulado["pimprod_Refeicao"],
        "tempo_minatend": acumulado["tempo_minatend"] or 0,
        "tempo_medatend": round(media_geral, 2),
        "tempo_maxatend": acumulado["tempo_maxatend"] or 0
    }

    session['nome'] = nome
    session['dados'] = dados

    return jsonify({"redirect_url": url_for('operadores_bp.render_operadores')})'''

@operadores_bp.route('/ChamadosSuporte/ticketsOperador', methods=['POST'])
def chamados_por_operador_periodo():
    try:
        data = request.json
        nome_operador = data.get("nome")
        dias = int(data.get("dias", 1))

        if not nome_operador:
            return jsonify({"status": "error", "message": "Nome do operador não fornecido."}), 400

        data_hoje = datetime.now().date()
        data_limite = data_hoje - timedelta(days=dias)

        chamados = db.session.query(
            Chamado.cod_chamado,
            Chamado.cod_solicitacao,
            Chamado.data_criacao,
            Chamado.data_finalizacao,
            Chamado.nome_grupo,
            Chamado.nome_status
        ).filter(
            cast(Chamado.data_criacao, Date) >= data_limite,
            cast(Chamado.data_criacao, Date) <= data_hoje,
            Chamado.operador == nome_operador
        ).all()

        lista_chamados = [{
            "cod_chamado": c.cod_chamado,
            "cod_solicitacao": c.cod_solicitacao,
            "data_criacao": c.data_criacao.strftime("%Y-%m-%d %H:%M:%S") if c.data_criacao else None,
            "data_finalizacao": c.data_finalizacao.strftime("%Y-%m-%d %H:%M:%S") if c.data_finalizacao else None,
            "nome_grupo": c.nome_grupo,
            "nome_status": c.nome_status
        } for c in chamados]

        return jsonify({
            "status": "success",
            "total_chamados": len(lista_chamados),
            "data_referencia": f"Últimos {dias} dias",
            "chamados": lista_chamados
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


'''@operadores_bp.route('/dadosCompletos', methods=['POST'])
def dados_completos_operador():
    OPERADORES_IDS = {
        "Matheus": 2021,
        "Renato": 2020,
        "Gustavo": 2022,
        "Raysa": 2023,
        "Danilo": 2025
    }

    data = request.get_json()
    nome = data.get('nome')
    dias_str = data.get('dias', '1')

    if not nome:
        return jsonify({"status": "error", "message": "Nome do operador não fornecido"}), 400

    operador_id = OPERADORES_IDS.get(nome)
    if not operador_id:
        return jsonify({"status": "error", "message": f"Operador '{nome}' não encontrado"}), 404

    # Parte 1: Tickets do Operador
    try:
        dias = int(dias_str)
        data_hoje = datetime.now().date()
        data_limite = data_hoje - timedelta(days=dias)

        chamados = db.session.query(
            Chamado.cod_chamado,
            Chamado.cod_solicitacao,
            Chamado.data_criacao,
            Chamado.data_finalizacao,
            Chamado.nome_grupo,
            Chamado.nome_status
        ).filter(
            cast(Chamado.data_criacao, Date) >= data_limite,
            cast(Chamado.data_criacao, Date) <= data_hoje,
            Chamado.operador == nome
        ).all()

        lista_chamados = [
            {
                "cod_chamado": c.cod_chamado,
                "cod_solicitacao": c.cod_solicitacao,
                "data_criacao": c.data_criacao.strftime("%Y-%m-%d %H:%M:%S") if c.data_criacao else None,
                "data_finalizacao": c.data_finalizacao.strftime("%Y-%m-%d %H:%M:%S") if c.data_finalizacao else None,
                "nome_grupo": c.nome_grupo,
                "nome_status": c.nome_status
            } for c in chamados
        ]

        total_chamados = len(lista_chamados)

    except Exception as e:
        return jsonify({"status": "error", "message": f"Erro ao buscar chamados: {str(e)}"}), 500

    # Parte 2: Performance do Operador
    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    if "access_token" not in auth_response:
        return jsonify({"status": "error", "message": "Falha na autenticação"}), 401

    access_token = auth_response["access_token"]
    hoje = datetime.now()
    ontem = hoje - timedelta(days=1)

    periodos = {
        "1": (ontem).strftime('%Y-%m-%d'),
        "7": (ontem - timedelta(days=6)).strftime('%Y-%m-%d'),
        "15": (ontem - timedelta(days=14)).strftime('%Y-%m-%d'),
        "30": (ontem - timedelta(days=29)).strftime('%Y-%m-%d'),
        "90": (ontem - timedelta(days=89)).strftime('%Y-%m-%d')
    }

    data_inicial = periodos.get(dias_str, periodos["1"])
    data_final = (hoje - timedelta(days=1)).strftime('%Y-%m-%d')

    class Params:
        initial_date = data_inicial
        final_date = data_final
        initial_hour = "00:00:00"
        final_hour = "23:59:59"
        week = ""
        agents = [operador_id]
        queues = [1]
        options = {
            "sort": {"data": -1},
            "offset": 0,
            "count": 1000
        }
        conf = {}

    response = utils.atendentePerformance(access_token, Params)
    dados_atendentes = response.get("result", {}).get("data", [])

    if not dados_atendentes:
        return jsonify({"status": "error", "message": "Nenhum dado encontrado para esse colaborador"}), 404

    acumulado = {
        "ch_atendidas": 0,
        "ch_naoatendidas": 0,
        "tempo_online": 0,
        "tempo_livre": 0,
        "tempo_servico": 0,
        "pimprod_Refeicao": 0,
        "tempo_minatend": None,
        "tempo_medatend": [],
        "tempo_maxatend": None
    }

    for item in dados_atendentes:
        acumulado["ch_atendidas"] += item.get("ch_atendidas", 0)
        acumulado["ch_naoatendidas"] += item.get("ch_naoatendidas", 0)
        acumulado["tempo_online"] += item.get("tempo_online", 0)
        acumulado["tempo_livre"] += item.get("tempo_livre", 0)
        acumulado["tempo_servico"] += item.get("tempo_servico", 0)
        acumulado["pimprod_Refeicao"] += item.get("pimprod_Refeicao", 0)

        if item.get("tempo_minatend") is not None:
            if acumulado["tempo_minatend"] is None or item["tempo_minatend"] < acumulado["tempo_minatend"]:
                acumulado["tempo_minatend"] = item["tempo_minatend"]

        if item.get("tempo_maxatend") is not None:
            if acumulado["tempo_maxatend"] is None or item["tempo_maxatend"] > acumulado["tempo_maxatend"]:
                acumulado["tempo_maxatend"] = item["tempo_maxatend"]

        if item.get("tempo_medatend") is not None:
            acumulado["tempo_medatend"].append(item["tempo_medatend"])

    media_geral = (
        sum(acumulado["tempo_medatend"]) / len(acumulado["tempo_medatend"])
        if acumulado["tempo_medatend"] else 0
    )

    dados = {
        "ch_atendidas": acumulado["ch_atendidas"],
        "ch_naoatendidas": acumulado["ch_naoatendidas"],
        "tempo_online": acumulado["tempo_online"],
        "tempo_livre": acumulado["tempo_livre"],
        "tempo_servico": acumulado["tempo_servico"],
        "pimprod_Refeicao": acumulado["pimprod_Refeicao"],
        "tempo_minatend": acumulado["tempo_minatend"] or 0,
        "tempo_medatend": round(media_geral, 2),
        "tempo_maxatend": acumulado["tempo_maxatend"] or 0
    }

    return jsonify({
        "status": "success",
        "nome": nome,
        "dados_performance": dados,
        "total_chamados": total_chamados,
        "chamados": lista_chamados
    })'''


