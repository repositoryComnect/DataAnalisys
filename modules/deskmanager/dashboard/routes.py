from flask import Blueprint, jsonify, request
from settings import endpoints
import requests, json, os
import calendar
from modules.deskmanager.authenticate.routes import token_desk
from datetime import datetime, date
from dateutil.parser import parse as parse_date
from application.models import db, Chamado
from sqlalchemy import extract, func


dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/ChamadosSuporte', methods=['POST'])
def listar_chamados_aberto():
    token_response = token_desk()
    
    try:
        # Faz a requisição para a API de chamados
        response = requests.post(
            'https://api.desk.ms/ChamadosSuporte/lista',
            headers={
                'Authorization': f'{token_response}',
                'Content-Type': 'application/json'
            },
            json={
                "Pesquisa":"", 	#Pesquisa por Assunto,Código,Descrição,Solicitante,Status,Operador ou Dados do Cliente
            "Tatual":"", 	#Opcional para uso com mais de 3000 registros, define a partir de qual registro exibir
            "Ativo":"EmAberto",	#Pode usar um texto pré definido ou o código do Status*
            "StatusSLA":"S", #S: Apenas com SLA, A: Apenas sem SLA, N: Com e Sem SLA (todos)
            "Colunas": 	#Colunas a serem exibidas, Caso não seja enviado trará todas
            {
                "Chave":"on",		#Chave do chamado
                "CodChamado":"on",	#Código de referência do chamado (mmaa-000000)
                "NomePrioridade":"on",	#Prioridade do chamado
                "DataCriacao":"on",	#Data da criação
                "HoraCriacao":"on",	#Hora da criação
                "DataFinalizacao":"on",	#Data da finalização
                "HoraFinalizacao":"on", #Hora da finalização
                "DataAlteracao":"on", 	#Data da Ultima Alteração
                "HoraAlteracao":"on", 	#Hora da Ultima Alteração
                "NomeStatus":"on",	#Nome do Status atual do chamado
                "Assunto":"on",	
                "Descricao":"on",
                "ChaveUsuario":"on",	#Código do Solicitante	
                "NomeUsuario":"on",		#Primeiro nome do Solicitante
                "SobrenomeUsuario":"on",	#Sobrenome do Solicitante
                "NomeCompletoSolicitante":"on", #Nome Completo do Solicitante
                "SolicitanteEmail":"on",	#Email do Solicitante
                "NomeOperador":"on",		#Primeiro nome do Operador
                "SobrenomeOperador":"on",	#Sobrenome do Operador
                "TotalAcoes":"on",		#Quantidade de ações realizadas no chamado
                "TotalAnexos":"on",
                "Sla":"on",			#Exibe as informações sobre o SLA (várias colunas serão exibidas)
                "CodGrupo":"on",		#Código do grupo de atendimento do chamado
                "NomeGrupo":"on",		#Nome do grupo de atendimento do chamado
                "CodSolicitacao":"on", 		#Código de Solicitação
                "CodSubCategoria":"on", 	#Código de Sub Categoria
                "CodTipoOcorrencia":"on", 	#Código do Tipo de Ocorrência
                "CodCategoriaTipo":"on", 	#Código do Tipo de Categoria
                "CodPrioridadeAtual":"on", 	#Código da Prioridade
                "CodStatusAtual":"on"	#Código do Status Atual
            },
            "Ordem": [	#Colunas para ordenação
                {
                "Coluna": "Chave",
                "Direcao": "true"	#true:ASC e false:DESC	
                }
            ]
            }
            )
        
        # Verifica se a requisição foi bem sucedida
        if response.status_code == 200:
            data = response.json()
            
            # Captura apenas o total do retorno
            total_chamados = data.get("total", "0")
            
            return jsonify({
                "status": "success",
                "total_chamados": total_chamados
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Erro na requisição",
                "status_code": response.status_code
            }), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao conectar com o servidor",
            "details": str(e)
        }), 500

@dashboard_bp.route('/ChamadosSuporte/finalizado', methods=['POST'])
def listar_chamados_finalizado():
    token_response = token_desk()
    
    try:
        # Faz a requisição para a API de chamados
        response = requests.post(
            'https://api.desk.ms/ChamadosSuporte/lista',
            headers={
                'Authorization': f'{token_response}',
                'Content-Type': 'application/json'
            },
            json={
                "Pesquisa":"", 	#Pesquisa por Assunto,Código,Descrição,Solicitante,Status,Operador ou Dados do Cliente
            "Tatual":"", 	#Opcional para uso com mais de 3000 registros, define a partir de qual registro exibir
            "Ativo":"000002",	#Pode usar um texto pré definido ou o código do Status*
            "StatusSLA":"S", #S: Apenas com SLA, A: Apenas sem SLA, N: Com e Sem SLA (todos)
            "Colunas": 	#Colunas a serem exibidas, Caso não seja enviado trará todas
            {
                "Chave":"on",		#Chave do chamado
                "CodChamado":"on",	#Código de referência do chamado (mmaa-000000)
                "NomePrioridade":"on",	#Prioridade do chamado
                "DataCriacao":"on",	#Data da criação
                "HoraCriacao":"on",	#Hora da criação
                "DataFinalizacao":"on",	#Data da finalização
                "HoraFinalizacao":"on", #Hora da finalização
                "DataAlteracao":"on", 	#Data da Ultima Alteração
                "HoraAlteracao":"on", 	#Hora da Ultima Alteração
                "NomeStatus":"on",	#Nome do Status atual do chamado
                "Assunto":"on",	
                "Descricao":"on",
                "ChaveUsuario":"on",	#Código do Solicitante	
                "NomeUsuario":"on",		#Primeiro nome do Solicitante
                "SobrenomeUsuario":"on",	#Sobrenome do Solicitante
                "NomeCompletoSolicitante":"on", #Nome Completo do Solicitante
                "SolicitanteEmail":"on",	#Email do Solicitante
                "NomeOperador":"on",		#Primeiro nome do Operador
                "SobrenomeOperador":"on",	#Sobrenome do Operador
                "TotalAcoes":"on",		#Quantidade de ações realizadas no chamado
                "TotalAnexos":"on",
                "Sla":"on",			#Exibe as informações sobre o SLA (várias colunas serão exibidas)
                "CodGrupo":"on",		#Código do grupo de atendimento do chamado
                "NomeGrupo":"on",		#Nome do grupo de atendimento do chamado
                "CodSolicitacao":"on", 		#Código de Solicitação
                "CodSubCategoria":"on", 	#Código de Sub Categoria
                "CodTipoOcorrencia":"on", 	#Código do Tipo de Ocorrência
                "CodCategoriaTipo":"on", 	#Código do Tipo de Categoria
                "CodPrioridadeAtual":"on", 	#Código da Prioridade
                "CodStatusAtual":"on"	#Código do Status Atual
            },
            "Ordem": [	#Colunas para ordenação
                {
                "Coluna": "Chave",
                "Direcao": "true"	#true:ASC e false:DESC	
                }
            ]
            }
            )
        
        # Verifica se a requisição foi bem sucedida
        if response.status_code == 200:
            data = response.json()
            
            # Captura apenas o total do retorno
            total_chamados = data.get("total", "0")
            
            return jsonify({
                "status": "success",
                "total_chamados": total_chamados
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Erro na requisição",
                "status_code": response.status_code
            }), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao conectar com o servidor",
            "details": str(e)
        }), 500

@dashboard_bp.route('/ChamadosSuporte/fila', methods=['POST'])
def listar_chamados_fila():
    token_response = token_desk()

    payload = {
        "Pesquisa": "",
        "Tatual": "",
        "Ativo": "NaFila",
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
            "CodSolicitacao": "off",
            "CodSubCategoria": "off",
            "CodTipoOcorrencia": "off",
            "CodCategoriaTipo": "off",
            "CodPrioridadeAtual": "off",
            "CodStatusAtual": "off"
        },
        "Ordem": [{
            "Coluna": "Chave",
            "Direcao": "true"
        }]
    }

    try:
        response = requests.post(
            'https://api.desk.ms/ChamadosSuporte/lista',
            headers={
                'Authorization': f'{token_response}',
                'Content-Type': 'application/json'
            },
            json=payload
        )
        # Verifica se a requisição foi bem sucedida
        if response.status_code == 200:
            data = response.json()
            
            # Captura apenas o total do retorno
            total_chamados = data.get("total", "0")
            
            return jsonify({
                "status": "success",
                "total_chamados": total_chamados
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Erro na requisição",
                "status_code": response.status_code
            }), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao conectar com o servidor",
            "details": str(e)
        }), 500

@dashboard_bp.route('/ChamadosSuporte/sla_andamento', methods=['POST'])
def listar_sla_andamento():
    token_response = token_desk()
    url = endpoints.LISTA_CHAMADOS_SUPORTE

    payload = {
        "Pesquisa": "",
        "Tatual": "",
        "Ativo": "EmAberto",
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
            "CodSolicitacao": "off",
            "CodSubCategoria": "off",
            "CodTipoOcorrencia": "off",
            "CodCategoriaTipo": "off",
            "CodPrioridadeAtual": "off",
            "CodStatusAtual": "off"
        },
        "Ordem": [{
            "Coluna": "Chave",
            "Direcao": "true"
        }]
    }

    try:
        response = requests.post(
            url,
            headers={
                'Authorization': f'{token_response}',
                'Content-Type': 'application/json'
            },
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            chamados = data.get("root", [])

            sla1_expirado = 0
            sla1_nao_expirado = 0
            sla2_expirado = 0
            sla2_nao_expirado = 0

            for chamado in chamados:
                sla1 = chamado.get("Sla1Expirado")
                sla2 = chamado.get("Sla2Expirado")

                if sla1 == "S":
                    sla1_expirado += 1
                elif sla1 == "N":
                    sla1_nao_expirado += 1

                if sla2 == "S":
                    sla2_expirado += 1
                elif sla2 == "N":
                    sla2_nao_expirado += 1

            return jsonify({
                "status": "success",
                "sla1_expirado": sla1_expirado,
                "sla1_nao_expirado": sla1_nao_expirado,
                "sla2_expirado": sla2_expirado,
                "sla2_nao_expirado": sla2_nao_expirado,
                "total": sla1_expirado + sla1_nao_expirado + sla2_expirado + sla2_nao_expirado
            })

        return jsonify({
            "status": "error",
            "message": "Erro na requisição",
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao conectar com o servidor",
            "details": str(e)
        }), 500

'''@dashboard_bp.route('/ChamadosSuporte/contagem_mes_atual', methods=['POST'])
def contar_chamados_mes_atual():
    token_response = token_desk()

    payload = {
    "Pesquisa": "",
    "Tatual": "",
    "Ativo": "Todos",          # Pode ser: Todos, EmAberto, Favoritos, Compartilhados, etc.
    "StatusSLA": "S",          # S: Apenas com SLA, A: Apenas sem SLA, N: Todos
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
        "CodStatusAtual": "on",
        # Adicione abaixo campos extras personalizados, se houver. Exemplo:
        # "_6313": "on"
    },
    "Ordem": [
        {
            "Coluna": "Chave",
            "Direcao": "true"  # true para ASC, false para DESC
        }
    ]
}


    # 3. Requisição para a API
    try:
        response = requests.post(
            'https://api.desk.ms/ChamadosSuporte/lista',
            headers={
                'Authorization': f'{token_response}',
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=30  # Timeout em segundos
        )

        response.raise_for_status()  # Lança exceção para status 4xx/5xx

        # 4. Processamento dos dados
        chamados = response.json().get("root", [])
        hoje = datetime(2025, 5, 1)
        total = sum(
            1 for chamado in chamados
            if _is_chamado_mes_atual(chamado, hoje)
        )

        return jsonify({
            "status": "success",
            "total_mes_atual": total,
            "mes_referencia": f"{hoje.month}/{hoje.year}"
        })

    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "message": "Erro na comunicação com a API Desk",
            "details": str(e)
        }), 500

def _is_chamado_mes_atual(chamado: dict, data_referencia: datetime) -> bool:
    """Verifica se o chamado foi finalizado no mês/ano de referência."""
    #if chamado.get('NomeStatus') != "Resolvido":
    #    return False
        
    data_str = chamado.get('DataFinalizacao')
    if not data_str:
        return False

    try:
        data_fim = datetime.strptime(data_str.split(' ')[0], '%Y-%m-%d')
        return (
            data_fim.month == data_referencia.month 
            and data_fim.year == data_referencia.year
        )
    except (ValueError, IndexError):
        return False'''

@dashboard_bp.route('/ChamadosSuporte/contagem_mes_atual', methods=['POST'])
def contar_chamados_mes_atual():
    try:
        # 1. Autenticação
        token_response = token_desk()
        if not token_response:
            return jsonify({"status": "error", "message": "Falha na autenticação"}), 401

        # 2. Configurar período de referência
        hoje = datetime.now()
        mes_referencia = f"{hoje.year}-{hoje.month:02d}"

        payload = {
                    "Pesquisa": "",
                    "Tatual": "",
                    "Ativo": "",          # Pode ser: Todos, EmAberto, Favoritos, Compartilhados, etc.
                    "StatusSLA": "S",          # S: Apenas com SLA, A: Apenas sem SLA, N: Todos
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
                        "CodStatusAtual": "on",
                        # Adicione abaixo campos extras personalizados, se houver. Exemplo:
                        # "_6313": "on"
                    },
                    "Ordem": [
                        {
                            "Coluna": "Chave",
                            "Direcao": "false"  # true para ASC, false para DESC
                        }
                    ]
                }
    # 3. Fazer requisição para a API Desk
        response = requests.post(
            'https://api.desk.ms/ChamadosSuporte/lista',
            headers={'Authorization': f'{token_response}', 'Content-Type': 'application/json'},
            json=payload,
        )
        response.raise_for_status()

        # 4. Salvar resposta completa em arquivo
        dados_completos = response.json()
        hoje = datetime.now()
        nome_arquivo = f"chamados_{hoje.strftime('%Y%m%d_%H%M%S')}.txt"
        caminho_arquivo = os.path.join('logs', nome_arquivo)
        
        # Criar diretório se não existir
        os.makedirs('logs', exist_ok=True)
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados_completos, f, ensure_ascii=False, indent=2)

        chamados_api = dados_completos.get("root", [])

        # 5. Processar e armazenar no banco (como antes)
        with db.session.begin():
            db.session.query(Chamado).delete()
            
            for chamado in chamados_api:
                data_criacao_str = chamado.get('DataCriacao', '').split(' ')[0]
                if data_criacao_str:
                    try:
                        data_criacao = datetime.strptime(data_criacao_str, '%Y-%m-%d').date()
                        novo_chamado = Chamado(
                            chave=chamado.get('Chave'),
                            cod_chamado=chamado.get('CodChamado'),
                            data_criacao=data_criacao,
                            nome_status=chamado.get('NomeStatus'),
                            nome_grupo = chamado.get('NomeGrupo'),
                            cod_solicitacao = chamado.get('CodSolicitacao'),
                            operador = chamado.get('NomeOperador'),
                            mes_referencia=f"{data_criacao.year}-{data_criacao.month:02d}",
                            data_importacao=datetime.now()
                        )
                        db.session.add(novo_chamado)
                    except ValueError as e:
                        print(f"Erro ao processar chamado {chamado.get('CodChamado')}: {str(e)}")
                        continue

        # 6. Contagens (como antes)
        hoje = datetime.now()
        total_mes_atual = Chamado.query.filter(
            db.extract('month', Chamado.data_criacao) == hoje.month,
            db.extract('year', Chamado.data_criacao) == hoje.year
        ).count()

        total_abertos = Chamado.query.filter(
            db.extract('month', Chamado.data_criacao) == hoje.month,
            db.extract('year', Chamado.data_criacao) == hoje.year,
            ~Chamado.nome_status.in_(["Resolvido", "Cancelado"])
        ).count()

        return jsonify({
            "status": "success",
            "total_mes_atual": total_mes_atual,
            "total_abertos": total_abertos,
            "mes_referencia": f"{hoje.month}/{hoje.year}",
            "arquivo_log": nome_arquivo,
            "registros_processados": len(chamados_api),
            "observacao": f"Dados completos salvos em {nome_arquivo}"
        })

    except requests.exceptions.RequestException as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Erro na comunicação com a API Desk",
            "details": str(e)
        }), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Erro inesperado",
            "details": str(e)
        }), 500

@dashboard_bp.route('/ChamadosSuporte/estatisticas_mensais', methods=['GET'])
def estatisticas_chamados():

    try:
        # Obter parâmetros com valores padrão
        ano = request.args.get('ano', default=datetime.now().year, type=int)
        mes = request.args.get('mes', default=datetime.now().month, type=int)
        
        # Consulta otimizada ao banco de dados
        resultados = db.session.query(
            Chamado.nome_status,
            func.count(Chamado.id).label('total')
        ).filter(
            extract('year', Chamado.data_criacao) == ano,
            extract('month', Chamado.data_criacao) == mes
        ).group_by(
            Chamado.nome_status
        ).all()

        # Formatar resposta para o gráfico
        labels = [r[0] for r in resultados]
        dados = [r[1] for r in resultados]
        
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
                "total": sum(dados)
            },
            "mes_referencia": f"{mes}/{ano}"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500
    
@dashboard_bp.route('/ChamadosSuporte/por_grupo_mes_atual', methods=['GET'])
def chamados_por_grupo_mes():

    try:
        hoje = datetime.now()

        # Consulta agrupando por grupo
        resultados = db.session.query(
            Chamado.nome_grupo,
            func.count(Chamado.id).label('total')
        ).filter(
            extract('month', Chamado.data_criacao) == hoje.month,
            extract('year', Chamado.data_criacao) == hoje.year
        ).group_by(
            Chamado.nome_grupo
        ).order_by(
            func.count(Chamado.id).desc()
        ).all()

        labels = [r[0] or "Sem Grupo" for r in resultados]
        dados = [r[1] for r in resultados]

        return jsonify({
            "status": "success",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": "Chamados por Grupo",
                    "data": dados,
                    "backgroundColor": [
                        '#007bff', '#6610f2', '#6f42c1',
                        '#e83e8c', '#fd7e14', '#20c997',
                        '#17a2b8', '#6c757d', '#343a40'
                    ] * len(labels)  # repete as cores se precisar
                }]
            },
            "mes_referencia": f"{hoje.month}/{hoje.year}"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao buscar dados por grupo",
            "details": str(e)
        }), 500
    
@dashboard_bp.route('/ChamadosSuporte/por_operador_mes_atual', methods=['POST'])
def chamados_por_operador_mes_atual():
    try:
        # Obtém o ano e mês atual
        hoje = datetime.now()
        ano_atual = hoje.year
        mes_atual = hoje.month

        # Consulta a contagem de chamados por operador no mês atual
        resultados = db.session.query(
            Chamado.operador,
            func.count(Chamado.id).label('total')
        ).filter(
            extract('year', Chamado.data_criacao) == ano_atual,
            extract('month', Chamado.data_criacao) == mes_atual
        ).group_by(
            Chamado.operador
        ).all()

        # Organiza os dados para o gráfico
        labels = [r[0] for r in resultados]
        dados = [r[1] for r in resultados]
        backgroundColor = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']

        # Retorna os dados em formato JSON
        return jsonify({
            'status': 'success',
            'data': {
                'labels': labels,
                'datasets': [{
                    'data': dados,
                    'backgroundColor': backgroundColor[:len(labels)]
                }]
            },
            'mes_referencia': f'{mes_atual}/{ano_atual}'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@dashboard_bp.route('/ChamadosSuporte/por_tipo_solicitacao_mes_atual', methods=['POST'])
def chamados_por_tipo_solicitacao_mes_atual():
    try:
        # Obtém o ano e mês atual
        hoje = datetime.now()
        ano_atual = hoje.year
        mes_atual = hoje.month

        # Códigos de tipos de solicitação e seus nomes
        tipos_desejados = ["000101", "000071", "000003", "000004", "000001"]
        mapeamento_tipos = {
            "000101": "Portal",
            "000071": "Interno",
            "000003": "E-mail",
            "000004": "Telefone",
            "000001": "Portal Solicitante"
        }

        # Consulta a contagem de chamados por tipo de solicitação
        resultados = db.session.query(
            Chamado.cod_solicitacao,
            func.count(Chamado.id).label('total')
        ).filter(
            extract('year', Chamado.data_criacao) == ano_atual,
            extract('month', Chamado.data_criacao) == mes_atual,
            Chamado.cod_solicitacao.in_(tipos_desejados)
        ).group_by(
            Chamado.cod_solicitacao
        ).all()

        if not resultados:
            return jsonify({
                'status': 'success',
                'data': {
                    'labels': [],
                    'datasets': [{
                        'data': [],
                        'backgroundColor': []
                    }]
                },
                'mes_referencia': f'{mes_atual}/{ano_atual}',
                'message': 'Nenhum dado encontrado para os tipos especificados.'
            })

        # Organiza os dados para o gráfico
        labels = [mapeamento_tipos.get(r[0], f"Tipo {r[0]}") for r in resultados]
        dados = [r[1] for r in resultados]
        backgroundColor = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']

        return jsonify({
            'status': 'success',
            'data': {
                'labels': labels,
                'datasets': [{
                    'data': dados,
                    'backgroundColor': backgroundColor[:len(labels)]
                }]
            },
            'mes_referencia': f'{mes_atual}/{ano_atual}'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@dashboard_bp.route('/ChamadosSuporte/abertos_vs_resolvidos', methods=['POST'])
def chamados_abertos_vs_resolvidos():
    try:
        hoje = datetime.now()
        ano = hoje.year
        mes = hoje.month

        # Corrige o range de dias válidos no mês
        _, ultimo_dia = calendar.monthrange(ano, mes)
        dias_do_mes = list(range(1, ultimo_dia + 1))

        total_por_dia = {dia: 0 for dia in dias_do_mes}
        resolvidos_por_dia = {dia: 0 for dia in dias_do_mes}

        # Abertos
        resultados_abertos = db.session.query(
            extract('day', Chamado.data_criacao).label('dia'),
            func.count(Chamado.id)
        ).filter(
            extract('year', Chamado.data_criacao) == ano,
            extract('month', Chamado.data_criacao) == mes
        ).group_by('dia').all()

        for dia, total in resultados_abertos:
            total_por_dia[int(dia)] = total

        # Resolvidos
        resultados_resolvidos = db.session.query(
            extract('day', Chamado.data_criacao).label('dia'),
            func.count(Chamado.id)
        ).filter(
            extract('year', Chamado.data_criacao) == ano,
            extract('month', Chamado.data_criacao) == mes,
            Chamado.nome_status == 'Resolvido'  # ajuste se for "Finalizado"
        ).group_by('dia').all()

        for dia, total in resultados_resolvidos:
            resolvidos_por_dia[int(dia)] = total

        return jsonify({
            'status': 'success',
            'labels': [str(d) for d in dias_do_mes],
            'datasets': [
                {
                    'label': 'Total de Chamados Abertos',
                    'data': [total_por_dia[d] for d in dias_do_mes],
                    'borderColor': 'blue',
                    'fill': False
                },
                {
                    'label': 'Chamados Resolvidos',
                    'data': [resolvidos_por_dia[d] for d in dias_do_mes],
                    'borderColor': 'green',
                    'fill': False
                }
            ],
            'mes_referencia': f"{mes:02d}/{ano}"
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
