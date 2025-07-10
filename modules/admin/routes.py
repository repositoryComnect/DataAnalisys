from flask import Blueprint, jsonify, request
import requests
import modules.delgrande.relatorios.utils as utils
from modules.deskmanager.authenticate.routes import token_desk
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
from application.models import db, Chamado, DesempenhoAtendente
from sqlalchemy import extract, func
from modules.delgrande.auth.utils import authenticate, authenticate_relatorio
from settings.endpoints import CREDENTIALS


admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

@admin_bp.route('/abertos_vs_admin_resolvido_periodo', methods=['POST'])
def relacao_admin_abertos_vs_resolvido_periodo():
    try:
        dados = request.get_json(force=True)
        dias = int(dados.get("dias", 7))
        data_limite = datetime.now() - timedelta(days=dias)

        total_por_dia = {}
        resolvidos_por_dia = {}

        resultados_abertos = db.session.query(
            func.date(Chamado.data_criacao).label('dia'),
            func.count(Chamado.id)
        ).filter(
            Chamado.data_criacao >= data_limite
        ).group_by('dia').all()

        for dia, total in resultados_abertos:
            total_por_dia[dia] = total  # salva como datetime.date

        resultados_resolvidos = db.session.query(
            func.date(Chamado.data_criacao).label('dia'),
            func.count(Chamado.id)
        ).filter(
            Chamado.data_criacao >= data_limite,
            Chamado.nome_status == 'Resolvido'
        ).group_by('dia').all()

        for dia, total in resultados_resolvidos:
            resolvidos_por_dia[dia] = total  # salva como datetime.date

        # União ordenada de datas (datetime.date)
        todos_os_dias = sorted(set(total_por_dia.keys()).union(resolvidos_por_dia.keys()))

        # Retorno com datas formatadas
        return jsonify({
            'status': 'success',
            'labels': [dia.strftime('%d/%m') for dia in todos_os_dias],
            'datasets': [
                {
                    'label': 'Total de Chamados Abertos',
                    'data': [total_por_dia.get(dia, 0) for dia in todos_os_dias],
                    'borderColor': 'rgba(255, 99, 132, 0.7)',
                    'fill': False
                },
                {
                    'label': 'Chamados Resolvidos',
                    'data': [resolvidos_por_dia.get(dia, 0) for dia in todos_os_dias],
                    'borderColor': 'rgba(75, 192, 75, 0.7)',
                    'fill': False
                }
            ]
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/v2/report/attendants_performance', methods=['POST'])
def importar_ligacoes_atendidas():

    try:
        # 1. Autenticar com usuário fixo
        auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
        if "access_token" not in auth_response:
            return jsonify({"status": "error", "message": "Falha na autenticação", "detalhes": auth_response}), 401

        access_token = auth_response["access_token"]

        hoje = datetime.now()

        # Obtém o primeiro dia do mês atual
        primeiro_dia_mes = datetime.now().replace(day=1)
    
        # Obtém o último dia do mês atual
        ultimo_dia_mes = (primeiro_dia_mes.replace(month=primeiro_dia_mes.month % 12 + 1, day=1) - timedelta(days=1))

        # 2. Montar parâmetros
        class Params:
            initial_date = primeiro_dia_mes.strftime('%Y-%m-%d')
            final_date = ultimo_dia_mes.strftime('%Y-%m-%d')
            initial_hour = "00:00:00"
            final_hour = "23:59:59"
            week = ""
            agents = [2020, 2021, 2022, 2023, 2024, 2025, 2028, 2029]
            queues = [1]
            options = {
                "sort": {"data": -1},
                "offset": 0,
                "count": 1000
            }
            conf = {}

        # 3. Requisição à API utilitária
        response = utils.atendentePerformance(access_token, Params)
        #print(response)
        dados_atendentes = response.get("result", {}).get("data", [])


        if not dados_atendentes:
            return jsonify({"status": "error", "message": "Nenhum dado retornado"}), 204

        # 4. Inserir no banco (com limpeza antes)
        with db.session.begin():
            db.session.query(DesempenhoAtendente).delete()

            for item in dados_atendentes:
                nome = item.get("atendente")
                data_str = item.get("data")
                try:
                    data = datetime.strptime(data_str, "%Y-%m-%d").date()
                except Exception:
                    continue

                novo = DesempenhoAtendente(
                    nome=nome,
                    chamadas_atendidas=item.get("ch_atendidas"),
                    data=data,
                    tempo_online=item.get("tempo_online"),
                    tempo_servico=item.get("tempo_servico"),
                    tempo_totalatend=item.get("tempo_totalatend"),
                )
                db.session.add(novo)

        # 6. CONSULTA AJUSTADA - Aqui está a mudança principal
        resultados = (
            db.session.query(
                DesempenhoAtendente.nome,
                db.func.sum(DesempenhoAtendente.chamadas_atendidas).label('total')
            )
            .filter(
                DesempenhoAtendente.data.between(
                    primeiro_dia_mes.date(),
                    ultimo_dia_mes.date()
                )
            )
            .group_by(DesempenhoAtendente.nome)
            .all()
        )

        dados_grafico = [
            {"nome": nome, "total": total}
            for nome, total in resultados
        ]

        return jsonify({
            "status": "success",
            "data": dados_grafico,
            "registros_importados": len(dados_atendentes)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Erro inesperado",
            "details": str(e)
        }), 500

# Rota que   
'''@admin_bp.route('/get/operadores', methods=['GET'])
def get_operadores():
    try:
        # Consulta apenas operadores do grupo 'SUPORTE B2B - COMNECT'
        operadores = db.session.query(
            Chamado.operador
        ).filter(
            Chamado.operador.isnot(None),
            Chamado.operador != '',
            Chamado.operador != 'Fabio',
            Chamado.operador != 'API',
            Chamado.operador != 'Caio',
            Chamado.operador != 'Paulo',
            Chamado.operador != 'Luciano',
            Chamado.operador != 'Alexandre',
            Chamado.operador != 'Chrysthyanne',
            Chamado.operador != 'Suporte',
            Chamado.nome_grupo == 'SUPORTE COMNEcT - N1'
        ).distinct().order_by(
            Chamado.operador
        ).all()

        # Extrai apenas os nomes dos operadores
        lista_operadores = [op[0] for op in operadores if op[0]]

        return jsonify({
            "status": "success",
            "operadores": lista_operadores,
            "total": len(lista_operadores)
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500'''

# Rota que traz total de chamados abertos no período de uma semana
@admin_bp.route('/ChamadosSuporteSemanal', methods=['POST'])
def listar_chamados_aberto_semanal():
    token_response = token_desk()

    try:
        # 1. Receber os dados enviados do frontend (ex: {"dias": 7})
        dados = request.get_json(force=True)  # force=True para garantir leitura como JSON
        dias = int(dados.get("dias", 7))  # padrão: 7 dias
        data_limite = datetime.now() - timedelta(days=dias)

        # 2. Requisição à API externa (sem filtro de data ainda)
        response = requests.post(
            'https://api.desk.ms/ChamadosSuporte/lista',
            headers={
                'Authorization': f'{token_response}',
                'Content-Type': 'application/json'
            },
            json={
                "Pesquisa": "",
                "Tatual": "",
                "Ativo": "Todos",
                "StatusSLA": "S",
                "Colunas": {
                    "Chave": "on",
                    "CodChamado": "on",
                    "NomePrioridade": "on",
                    "DataCriacao": "on",
                    "HoraCriacao": "on",
                    "DataFinalizacao": "on",
                    "HoraFinalizacao": "on",
                    "DataAlteracao": "on",
                    "HoraAlteracao": "on",
                    "NomeStatus": "on",
                    "Assunto": "on",
                    "Descricao": "on",
                    "ChaveUsuario": "on",
                    "NomeUsuario": "on",
                    "SobrenomeUsuario": "on",
                    "NomeCompletoSolicitante": "on",
                    "SolicitanteEmail": "on",
                    "NomeOperador": "on",
                    "SobrenomeOperador": "on",
                    "TotalAcoes": "on",
                    "TotalAnexos": "on",
                    "Sla": "on",
                    "CodGrupo": "on",
                    "NomeGrupo": "on",
                    "CodSolicitacao": "on",
                    "CodSubCategoria": "on",
                    "CodTipoOcorrencia": "on",
                    "CodCategoriaTipo": "on",
                    "CodPrioridadeAtual": "on",
                    "CodStatusAtual": "on"
                },
                "Ordem": [
                    {
                        "Coluna": "Chave",
                        "Direcao": "true"
                    }
                ]
            }
        )

        # 3. Verificação da resposta
        if response.status_code != 200:
            return jsonify({
                "status": "error",
                "message": "Erro na requisição",
                "status_code": response.status_code
            }), response.status_code

        # 4. Processar os dados recebidos da API
        data = response.json()
        chamados = data.get("root", [])

        # 5. Filtrar por data de criação
        chamados_filtrados = [
            ch for ch in chamados
            if "DataCriacao" in ch and datetime.strptime(ch["DataCriacao"], "%Y-%m-%d") >= data_limite
        ]

        # 6. Retornar contagem filtrada
        return jsonify({
            "status": "success",
            "total_chamados": len(chamados_filtrados)
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Erro interno",
            "details": str(e)
        }), 500

# Rota que traz total de chamados finalizados na semana
@admin_bp.route('/ChamadosSuporte/finalizadoSemanal', methods=['POST'])
def listar_chamados_finalizado_semanal():

    token_response = token_desk()

    try:
        # 1. Lê o valor de dias (ex: {"dias": 7}) do frontend
        dados = request.get_json(force=True)
        dias = int(dados.get("dias", 7))  # Padrão: 7 dias
        data_limite = datetime.now() - timedelta(days=dias)

        # 2. Requisição para API de chamados finalizados
        response = requests.post(
            'https://api.desk.ms/ChamadosSuporte/lista',
            headers={
                'Authorization': f'{token_response}',
                'Content-Type': 'application/json'
            },
            json={
                "Pesquisa": "",
                "Tatual": "",
                "Ativo": "000002",  # Status finalizado (ou outro código de finalização)
                "StatusSLA": "S",
                "Colunas": {
                    "Chave": "on",
                    "CodChamado": "on",
                    "NomePrioridade": "on",
                    "DataCriacao": "on",
                    "HoraCriacao": "on",
                    "DataFinalizacao": "on",
                    "HoraFinalizacao": "on",
                    "DataAlteracao": "on",
                    "HoraAlteracao": "on",
                    "NomeStatus": "on",
                    "Assunto": "on",
                    "Descricao": "on",
                    "ChaveUsuario": "on",
                    "NomeUsuario": "on",
                    "SobrenomeUsuario": "on",
                    "NomeCompletoSolicitante": "on",
                    "SolicitanteEmail": "on",
                    "NomeOperador": "on",
                    "SobrenomeOperador": "on",
                    "TotalAcoes": "on",
                    "TotalAnexos": "on",
                    "Sla": "on",
                    "CodGrupo": "on",
                    "NomeGrupo": "on",
                    "CodSolicitacao": "on",
                    "CodSubCategoria": "on",
                    "CodTipoOcorrencia": "on",
                    "CodCategoriaTipo": "on",
                    "CodPrioridadeAtual": "on",
                    "CodStatusAtual": "on"
                },
                "Ordem": [
                    {
                        "Coluna": "Chave",
                        "Direcao": "true"
                    }
                ]
            }
        )

        if response.status_code != 200:
            return jsonify({
                "status": "error",
                "message": "Erro na requisição",
                "status_code": response.status_code
            }), response.status_code

        # 3. Processar dados da resposta
        data = response.json()
        chamados = data.get("root", [])

        # 4. Filtrar por data de finalização
        chamados_filtrados = [
            ch for ch in chamados
            if "DataFinalizacao" in ch and datetime.strptime(ch["DataFinalizacao"], "%Y-%m-%d") >= data_limite
        ]

        # 5. Retornar resultado
        return jsonify({
            "status": "success",
            "total_chamados": len(chamados_filtrados)
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Erro interno",
            "details": str(e)
        }), 500

# Rota que traz os tickets por canal pelos períodos de 7, 15, 30 e 90 dias  
@admin_bp.route('/ChamadosSuporte/ticketsCanal', methods=['POST'])
def chamados_tickets_canal():
    try:
        dias = int(request.json.get("dias", 7))  # valor padrão: últimos 30 dias
        data_limite = datetime.now() - timedelta(days=dias)

        tipos_desejados = ['000003', '000101', '000004', '000060', '000001', '000071']
        mapeamento_tipos = {
            '000101': 'Portal Comnect',
            '000071': 'Interno',
            '000003': 'E-mail',
            '000004': 'Telefone',
            '000001': 'Portal Solicitante',
            '000060': 'WhatsApp'
        }

        # Consulta agrupando por tipo e dia
        resultados = db.session.query(
            Chamado.cod_solicitacao,
            func.date(Chamado.data_criacao).label('dia'),
            func.count(Chamado.id)
        ).filter(
            Chamado.cod_solicitacao.in_(tipos_desejados),
            Chamado.data_criacao >= data_limite,
            #Chamado.data_finalizacao.is_(None),
            #Chamado.nome_status.notin_(['Cancelado', 'Resolvido'])  # caso queira filtrar
        ).group_by(
            Chamado.cod_solicitacao,
            func.date(Chamado.data_criacao)
        ).order_by(func.date(Chamado.data_criacao)).all()

        # Gerar lista contínua de dias
        hoje = datetime.now().date()
        lista_dias = [data_limite.date() + timedelta(days=i) for i in range((hoje - data_limite.date()).days + 1)]
        labels = [dia.strftime('%d/%m') for dia in lista_dias]

        # Organizar dados por tipo
        dados_agrupados = {cod: {} for cod in tipos_desejados}
        for cod, dia, total in resultados:
            dados_agrupados[cod][dia] = total

        cores = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']

        datasets = []
        for i, cod in enumerate(tipos_desejados):
            dados = [dados_agrupados[cod].get(d, 0) for d in lista_dias]
            datasets.append({
                'label': mapeamento_tipos.get(cod, cod),
                'data': dados,
                'backgroundColor': cores[i],
                'borderColor': cores[i],
                'fill': False,
                'tension': 0.3,
                'borderWidth': 2
            })

        return jsonify({
            'status': 'success',
            'data': {
                'labels': labels,
                'datasets': datasets
            },
            'data_referencia': f"Últimos {dias} dias"
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/ChamadosSuporte/ticketsOperador', methods=['POST'])
def chamados_por_operador_periodo():
    try:
        dias = int(request.json.get("dias", 7))  
        data_limite = datetime.now() - timedelta(days=dias)

        # Consulta todos os chamados criados no período, finalizados ou não
        resultados = db.session.query(
            Chamado.operador,
            func.count(Chamado.id).label('total')
        ).filter(
            Chamado.data_criacao >= data_limite
        ).group_by(
            Chamado.operador
        ).order_by(
            func.count(Chamado.id).desc()
        ).all()

        # Organiza os dados para o gráfico
        labels = [r[0] if r[0] else 'Sem operador' for r in resultados]
        dados = [r[1] for r in resultados]

        # Gera cores aleatórias distintas
        def gerar_cores_hex(n):
            import random
            random.seed(42)
            return [f'#{random.randint(0, 0xFFFFFF):06x}' for _ in range(n)]

        backgroundColor = gerar_cores_hex(len(labels))

        return jsonify({
            'status': 'success',
            'data': {
                'labels': labels,
                'datasets': [{
                    'data': dados,
                    'backgroundColor': backgroundColor
                }]
            },
            'data_referencia': f'Últimos {dias} dias'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@admin_bp.route('/ChamadosSuporte/estatisticas_mensais', methods=['POST'])
def estatisticas_chamados_periodos():
    try:
        dados = request.get_json(force=True)
        dias = int(dados.get("dias", 1))  
        data_limite = datetime.now() - timedelta(days=dias)

        chamados_abertos = db.session.query(
            Chamado.chave, 
            Chamado.nome_status,
            Chamado.nome_grupo,
            Chamado.data_criacao
        ).filter(
            Chamado.data_criacao >= data_limite,
            ~Chamado.nome_status.in_(["Cancelado"])
        ).all()

        status_counts = {}
        grupos = set()

        for chamado in chamados_abertos:
            status = chamado.nome_status
            grupo = chamado.nome_grupo
            grupos.add(grupo)
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1

        labels = list(status_counts.keys())
        dados = list(status_counts.values())

        return jsonify({
            "status": "success",
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": dados,
                    "backgroundColor": [
                        '#FF6384', '#36A2EB', '#FFCE56',
                        '#4BC0C0', '#9966FF', '#FF9F40'
                    ]
                }],
                "total": sum(dados),
                "grupos": list(grupos)
            },
            "chamados_abertos": [
                {
                    "chave": chamado.chave,
                    "nome_status": chamado.nome_status,
                    "nome_grupo": chamado.nome_grupo
                } for chamado in chamados_abertos
            ]
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500