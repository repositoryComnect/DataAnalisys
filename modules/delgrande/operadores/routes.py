from flask import Blueprint, jsonify, request, render_template, url_for, session
import modules.delgrande.relatorios.utils as utils
from application.models import db, DesempenhoAtendente, DesempenhoAtendenteVyrtos, PerformanceColaboradores, PesquisaSatisfacao
from modules.delgrande.auth.utils import authenticate, authenticate_relatorio
from application.models import Chamado
from settings.endpoints import CREDENTIALS
from datetime import datetime, timedelta
from sqlalchemy import func, cast, Date, and_


operadores_bp = Blueprint('operadores_bp', __name__, url_prefix='/operadores')


'''@operadores_bp.route('/performanceColaboradores', methods=['POST'])
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
    dias_str = str(data.get('dias', '1'))

    operador_id = OPERADORES_IDS.get(nome)

    # Autenticação
    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    if "access_token" not in auth_response:
        return jsonify({"status": "error", "message": "Falha na autenticação"}), 401

    access_token = auth_response["access_token"]

    hoje = datetime.now()
    ontem = hoje - timedelta(days=1)

    # Ajuste no cálculo das datas
    periodos = {
        "1": (ontem).strftime('%Y-%m-%d'),  # Ontem
        "7": (hoje - timedelta(days=6)).strftime('%Y-%m-%d'),  # Inclui 7 dias (ontem + hoje)
        "15": (hoje - timedelta(days=14)).strftime('%Y-%m-%d'),  # Últimos 15 dias
        "30": (hoje - timedelta(days=29)).strftime('%Y-%m-%d'),  # Últimos 30 dias
        "90": (hoje - timedelta(days=89)).strftime('%Y-%m-%d')  # Últimos 90 dias
    }

    # Pega a data inicial com base no parâmetro "dias" ou o valor padrão "1"
    data_inicial = periodos.get(dias_str, periodos["1"])
    data_final = (hoje - timedelta(days=1)).strftime('%Y-%m-%d')  # Ontem

    # Parâmetros para a consulta
    class Params:
        initial_date = data_inicial
        final_date = data_final
        initial_hour = "00:00:00"
        final_hour = "23:59:59"
        fixed = 0
        week = ""
        agents = [operador_id]
        queues = [1]
        options = {"sort": {"data": -1}, "offset": 0, "count": 1000}
        conf = {}

    # Chama a função de performance
    response = utils.atendentePerformance(access_token, Params)
    print(response)

    # Processa os dados de atendentes
    dados_atendentes = response.get("result", {}).get("data", [])
    print(dados_atendentes)

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

    # Itera sobre os dados recebidos e acumula os valores
    for item in dados_atendentes:
        acumulado["ch_atendidas"] += int(item.get("ch_atendidas") or 0)
        acumulado["ch_naoatendidas"] += int(item.get("ch_naoatendidas") or 0)
        acumulado["tempo_online"] += int(item.get("tempo_online") or 0)
        acumulado["tempo_livre"] += int(item.get("tempo_livre") or 0)
        acumulado["tempo_servico"] += int(item.get("tempo_servico") or 0)
        acumulado["pimprod_Refeicao"] += int(item.get("pimprod_Refeicao") or 0)

        if item.get("tempo_minatend") is not None:
            acumulado["tempo_minatend"] = (
                item["tempo_minatend"]
                if acumulado["tempo_minatend"] is None
                else min(acumulado["tempo_minatend"], item["tempo_minatend"])
            )

        if item.get("tempo_maxatend") is not None:
            acumulado["tempo_maxatend"] = (
                item["tempo_maxatend"]
                if acumulado["tempo_maxatend"] is None
                else max(acumulado["tempo_maxatend"], item["tempo_maxatend"])
            )

        if item.get("tempo_medatend") is not None:
            acumulado["tempo_medatend"].append(item["tempo_medatend"])

    # Calcula a média do tempo de atendimento
    media_geral = (
        sum(acumulado["tempo_medatend"]) / len(acumulado["tempo_medatend"])
        if acumulado["tempo_medatend"] else 0
    )

    # Organiza os dados para o retorno
    dados = {
        "periodo": dias_str,
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

    return jsonify({"status": "success", "dados": dados})'''

@operadores_bp.route('/performanceColaboradoresRender', methods=['POST'])
def performance_colaboradores_render():
    OPERADORES_IDS = {
        "Renato": 2020,
        "Matheus": 2021,
        "Gustavo": 2022,
        "Raysa": 2023,
        "Lucas": 2024,
        "Danilo": 2025,
        "Henrique": 2028,
        "Rafael": 2029
        }

    data = request.get_json()
    nome = data.get('nome')
    print(nome)

    '''if not nome:
        return jsonify({"status": "error", "message": "Nome do operador não fornecido"}), 400'''

    operador_id = OPERADORES_IDS.get(nome)
    if not operador_id:
        operador_id = ""
        #return jsonify({"status": "error", "message": f"Operador '{nome}' não encontrado"}), 404

    # Define a data (ontem)
    hoje = datetime.now().date()

    # Busca os registros no banco
    registros = PerformanceColaboradores.query.filter_by(operador_id=operador_id, data=hoje).all()

    # Inicializa os acumuladores
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

    for item in registros:
        acumulado["ch_atendidas"] += item.ch_atendidas
        acumulado["ch_naoatendidas"] += item.ch_naoatendidas
        acumulado["tempo_online"] += item.tempo_online
        acumulado["tempo_livre"] += item.tempo_livre
        acumulado["tempo_servico"] += item.tempo_servico
        acumulado["pimprod_Refeicao"] += item.pimprod_refeicao

        if item.tempo_minatend is not None:
            acumulado["tempo_minatend"] = (
                item.tempo_minatend
                if acumulado["tempo_minatend"] is None
                else min(acumulado["tempo_minatend"], item.tempo_minatend)
            )

        if item.tempo_maxatend is not None:
            acumulado["tempo_maxatend"] = (
                item.tempo_maxatend
                if acumulado["tempo_maxatend"] is None
                else max(acumulado["tempo_maxatend"], item.tempo_maxatend)
            )

        if item.tempo_medatend is not None:
            acumulado["tempo_medatend"].append(item.tempo_medatend)

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

@operadores_bp.route('/performanceColaboradores', methods=['POST'])
def get_performance_colaboradores():
    data = request.get_json()
    nome = data.get('nome', '').strip().title()  # normaliza o nome
    dias_str = str(data.get('dias', '1'))

    if not nome:
        return jsonify({"status": "error", "message": "Nome do operador não fornecido"}), 400

    # Busca o operador_id diretamente no banco usando o nome
    operador = PerformanceColaboradores.query.filter_by(name=nome).first()

    if not operador:
        return jsonify({"status": "error", "message": f"Operador '{nome}' não encontrado"}), 404

    operador_id = operador.operador_id

    hoje = datetime.now().date()
    ontem = hoje - timedelta(days=1)

    try:
        dias = int(dias_str)
    except ValueError:
        return jsonify({"status": "error", "message": "O valor de 'dias' deve ser um número inteiro"}), 400

    data_inicial = hoje - timedelta(days=dias)

    registros = PerformanceColaboradores.query.filter(
        PerformanceColaboradores.operador_id == operador_id,
        PerformanceColaboradores.data >= data_inicial,
        PerformanceColaboradores.data <= hoje
    ).all()


    # Inicializa os acumuladores
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

    for r in registros:
        acumulado["ch_atendidas"] += r.ch_atendidas
        acumulado["ch_naoatendidas"] += r.ch_naoatendidas
        acumulado["tempo_online"] += r.tempo_online
        acumulado["tempo_livre"] += r.tempo_livre
        acumulado["tempo_servico"] += r.tempo_servico
        acumulado["pimprod_Refeicao"] += r.pimprod_refeicao

        if r.tempo_minatend is not None:
            acumulado["tempo_minatend"] = r.tempo_minatend if acumulado["tempo_minatend"] is None else min(acumulado["tempo_minatend"], r.tempo_minatend)

        if r.tempo_maxatend is not None:
            acumulado["tempo_maxatend"] = r.tempo_maxatend if acumulado["tempo_maxatend"] is None else max(acumulado["tempo_maxatend"], r.tempo_maxatend)

        if r.tempo_medatend is not None:
            acumulado["tempo_medatend"].append(r.tempo_medatend)

    media_geral = (
        sum(acumulado["tempo_medatend"]) / len(acumulado["tempo_medatend"])
        if acumulado["tempo_medatend"] else 0
    )

    dados = {
        "periodo": dias_str,
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

    return jsonify({"status": "success", "dados": dados})

'''@operadores_bp.route('/performanceColaboradores', methods=['POST'])
def get_performance_colaboradores():
    OPERADORES_IDS = {
        "Renato": 2020,
        "Matheus": 2021,
        "Gustavo": 2022,
        "Raysa": 2023,
        "Lucas": 2024,
        "Danilo": 2025,
        "Henrique": 2028,
        "Rafael": 2029
    }

    data = request.get_json()
    nome = data.get('nome')
    dias_str = str(data.get('dias', '1'))

    operador_id = OPERADORES_IDS.get(nome)
    if not operador_id:
        return jsonify({"status": "error", "message": "Operador não encontrado"}), 404

    hoje = datetime.now().date()
    ontem = hoje - timedelta(days=1)

    # Verifica se o usuário está pedindo os dados para 90 dias
    if dias_str == "90":
        # Autentica e faz o request à API externa para obter os dados dos últimos 90 dias
        auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
        if "access_token" not in auth_response:
            return jsonify({"status": "error", "message": "Falha na autenticação"}), 401

        access_token = auth_response["access_token"]
        data_inicial = hoje - timedelta(days=89)
        data_final = ontem

        class Params:
            initial_date = data_inicial
            final_date = data_final
            initial_hour = "00:00:00"
            final_hour = "23:59:59"
            fixed = 0
            week = ""
            agents = [operador_id]
            queues = [1]
            options = {"sort": {"data": -1}, "offset": 0, "count": 1000}
            conf = {}

        # Chama a API externa para pegar os dados de performance
        response = utils.atendentePerformance(access_token, Params)
        dados_atendentes = response.get("result", {}).get("data", [])

        # Armazena os dados no banco de dados
        for item in dados_atendentes:
            data_registro = datetime.strptime(item["data"], "%Y-%m-%d").date()
            registro = PerformanceColaboradores.query.filter_by(operador_id=operador_id, data=data_registro).first()

            if not registro:
                # Caso o registro ainda não exista, cria um novo
                registro = PerformanceColaboradores(
                    operador_id=operador_id,
                    data=data_registro,
                    ch_atendidas=item.get("ch_atendidas", 0),
                    ch_naoatendidas=item.get("ch_naoatendidas", 0),
                    tempo_online=item.get("tempo_online", 0),
                    tempo_livre=item.get("tempo_livre", 0),
                    tempo_servico=item.get("tempo_servico", 0),
                    pimprod_refeicao=item.get("pimprod_Refeicao", 0),
                    tempo_minatend=item.get("tempo_minatend"),
                    tempo_medatend=item.get("tempo_medatend"),
                    tempo_maxatend=item.get("tempo_maxatend")
                )
                db.session.add(registro)

        # Confirma a transação no banco
        db.session.commit()
        return jsonify({"status": "success", "message": "Dados de 90 dias armazenados com sucesso."})

    else:
        # Se não for 90 dias, realiza a consulta no banco de dados
        dias = int(dias_str)
        data_inicial = hoje - timedelta(days=dias)
        registros = PerformanceColaboradores.query.filter(
            PerformanceColaboradores.operador_id == operador_id,
            PerformanceColaboradores.data >= data_inicial,
            PerformanceColaboradores.data <= ontem
        ).all()

        # Inicializa os acumuladores para os dados
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

        # Processa os dados dos registros encontrados
        for r in registros:
            acumulado["ch_atendidas"] += r.ch_atendidas
            acumulado["ch_naoatendidas"] += r.ch_naoatendidas
            acumulado["tempo_online"] += r.tempo_online
            acumulado["tempo_livre"] += r.tempo_livre
            acumulado["tempo_servico"] += r.tempo_servico
            acumulado["pimprod_Refeicao"] += r.pimprod_refeicao

            if r.tempo_minatend is not None:
                acumulado["tempo_minatend"] = r.tempo_minatend if acumulado["tempo_minatend"] is None else min(acumulado["tempo_minatend"], r.tempo_minatend)
            if r.tempo_maxatend is not None:
                acumulado["tempo_maxatend"] = r.tempo_maxatend if acumulado["tempo_maxatend"] is None else max(acumulado["tempo_maxatend"], r.tempo_maxatend)
            if r.tempo_medatend is not None:
                acumulado["tempo_medatend"].append(r.tempo_medatend)

        # Calcula a média do tempo de atendimento
        media_geral = (
            sum(acumulado["tempo_medatend"]) / len(acumulado["tempo_medatend"])
            if acumulado["tempo_medatend"] else 0
        )

        # Organiza os dados para o retorno
        dados = {
            "periodo": dias_str,
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

        return jsonify({"status": "success", "dados": dados})'''

@operadores_bp.route('/colaboradores', methods=['GET'])
def render_operadores():
    nome = session.get('nome')
    dados = session.get('dados')
    total_chamados = session.get('total_chamados', 0)  # Pega da sessão, default 0

    if not nome or not dados:
        return "Dados não encontrados na sessão", 400

    return render_template('colaboradores.html', nome=nome, dados=dados, total_chamados=total_chamados)

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

@operadores_bp.route('/ChamadosSuporte/ticketsTelefoneVsAtendidas', methods=['POST'])
def chamados_telefone_vs_atendidas():
    try:
        dias_str = str(request.json.get("dias", "1"))
        nome_operador = request.json.get("nome", "").strip().title()

        if not nome_operador:
            return jsonify({'status': 'error', 'message': 'Nome do operador não fornecido'}), 400

        operador = PerformanceColaboradores.query.filter_by(name=nome_operador).first()
        if not operador:
            return jsonify({'status': 'error', 'message': f"Operador '{nome_operador}' não encontrado"}), 404

        operador_id = operador.operador_id

        hoje = datetime.now().date()
        ontem = hoje - timedelta(days=1)

        periodos = {
            "1": hoje,
            "7": hoje - timedelta(days=7),
            "15": hoje - timedelta(days=15),
            "30": hoje - timedelta(days=30),
            "90": hoje - timedelta(days=90),
            "180": hoje -  timedelta(days=180)
        }

        data_inicial = periodos.get(dias_str, periodos["1"])
        data_final = hoje

        lista_dias = [
            data_inicial + timedelta(days=i)
            for i in range((data_final - data_inicial).days + 1)
        ]
        labels = [dia.strftime('%d/%m') for dia in lista_dias]

        # === TICKETS (com filtro para remover cancelados)
        chamados_result = db.session.query(
            func.date(Chamado.data_criacao).label('dia'),
            func.count(Chamado.id)
        ).filter(
            Chamado.cod_solicitacao == '000004',
            Chamado.operador == nome_operador,
            #Chamado.nome_status != 'Cancelado',
            func.date(Chamado.data_criacao).in_(lista_dias)
        ).group_by(
            func.date(Chamado.data_criacao)
        ).all()

        chamados_por_dia = {dia: total for dia, total in chamados_result}
        dados_chamados = [chamados_por_dia.get(dia, 0) for dia in lista_dias]

        # === LIGAÇÕES
        atendimentos_result = db.session.query(
            PerformanceColaboradores.data,
            func.sum(PerformanceColaboradores.ch_atendidas)
        ).filter(
            PerformanceColaboradores.operador_id == operador_id,
            PerformanceColaboradores.data >= data_inicial,
            PerformanceColaboradores.data <= data_final
        ).group_by(
            PerformanceColaboradores.data
        ).all()

        atendimentos_por_dia_map = {data: total for data, total in atendimentos_result}
        atendimentos_por_dia = [atendimentos_por_dia_map.get(dia, 0) for dia in lista_dias]

        return jsonify({
            'status': 'success',
            'data': {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Tickets',
                        'data': dados_chamados,
                        'backgroundColor': 'rgba(255, 99, 132, 0.5)',
                        'borderColor': 'rgba(255, 99, 132, 1)',
                        'fill': False,
                        'tension': 0.3
                    },
                    {
                        'label': 'Ligações',
                        'data': atendimentos_por_dia,
                        'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                        'borderColor': 'rgba(54, 162, 235, 1)',
                        'fill': False,
                        'tension': 0.3
                    }
                ]
            }
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@operadores_bp.route('/GetSlaOperador', methods=['POST'])
def get_sla_operador():
    data = request.get_json()
    nome = data.get('nome')

    dias = int(data.get('dias', 1))

    data_inicio = datetime.now() - timedelta(days=dias)

    # Filtro com operador, período e grupo de suporte
    chamados = Chamado.query.filter(
        Chamado.nome_grupo.ilike('SUPORTE COMNEcT - N1'),
        Chamado.nome_status != 'Cancelado',
        Chamado.operador == nome,
        Chamado.data_criacao >= data_inicio
    ).all()

    # Filtra apenas os expirados
    chamados_expirados = [
        c for c in chamados if c.sla_atendimento == 'S' or c.sla_resolucao == 'S'
    ]

    expirados_atendimento = sum(1 for c in chamados if c.sla_atendimento == 'S')
    expirados_resolucao = sum(1 for c in chamados if c.sla_resolucao == 'S')
    


    return jsonify({
        "chamados": [c.to_dict() for c in chamados_expirados],
        "expirados_atendimento": expirados_atendimento,
        "expirados_resolucao": expirados_resolucao,
        "codigos_atendimento": [c.cod_chamado for c in chamados_expirados if c.sla_atendimento == 'S'],
        "codigos_resolucao": [c.cod_chamado for c in chamados_expirados if c.sla_resolucao == 'S']
    })

@operadores_bp.route('/pSatisfacaoOperador', methods=['POST'])
def listar_p_satisfacao():
    data = request.get_json()
    dias = int(data.get('dias', 1))
    nome = data.get('nome')
    data_limite = (datetime.now() - timedelta(days=dias)).date()  # só data, sem hora

    # Filtro base
    filtro_base = [
        PesquisaSatisfacao.data_resposta >= data_limite,
        PesquisaSatisfacao.operador.ilike(f"{nome}%")  # ilike = case-insensitive
    ]

    # Total de pesquisas do operador no período
    total_pesquisas = db.session.query(func.count()).filter(*filtro_base).scalar()

    # Total com alternativa respondida
    respondidas = db.session.query(func.count()).filter(
        *filtro_base,
        PesquisaSatisfacao.alternativa.isnot(None),
        func.length(PesquisaSatisfacao.alternativa) > 0
    ).scalar()

    nao_respondidas = total_pesquisas - respondidas

    percentual_respondidas = round((respondidas / total_pesquisas) * 100, 2) if total_pesquisas else 0
    percentual_nao_respondidas = 100 - percentual_respondidas if total_pesquisas else 0

    # Lista das alternativas preenchidas para esse operador
    alternativas_respondidas = db.session.query(PesquisaSatisfacao.alternativa).filter(
        *filtro_base,
        PesquisaSatisfacao.alternativa.isnot(None),
        func.length(PesquisaSatisfacao.alternativa) > 0
    ).all()

    lista_alternativas = [alt[0] for alt in alternativas_respondidas]

    # Adicione isso antes do return
    comentarios = db.session.query(PesquisaSatisfacao.resposta_dissertativa).filter(
        and_(
            PesquisaSatisfacao.data_resposta >= data_limite,
            PesquisaSatisfacao.operador.ilike(f"{nome}%"),
            PesquisaSatisfacao.resposta_dissertativa.isnot(None),
            func.length(PesquisaSatisfacao.resposta_dissertativa) > 0
        )
    ).all()

    lista_comentarios = [c[0] for c in comentarios]

    return jsonify({
        "status": "success",
        "operador": nome,
        "total": total_pesquisas,
        "respondidas": respondidas,
        "nao_respondidas": nao_respondidas,
        "percentual_respondidas": percentual_respondidas,
        "percentual_nao_respondidas": percentual_nao_respondidas,
        "alternativas": lista_alternativas,
        "comentarios": lista_comentarios
    })
