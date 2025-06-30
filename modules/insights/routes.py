from flask import Blueprint, jsonify, render_template, request, url_for
import requests
from modules.deskmanager.authenticate.routes import token_desk
from datetime import datetime, timedelta
from application.models import Chamado


insights_bp = Blueprint('/insights_bp', __name__, url_prefix='/insights')
    
@insights_bp.route('/ChamadosSuporte', methods=['POST'])
def listar_chamados_criados():
    try:
        dias = int(request.json.get("dias", 1))  # padrão: 1 dia
        hoje = datetime.now().date()
        data_inicio = hoje - timedelta(days=dias)

        # Combina datas com hora mínima e máxima do dia
        inicio = datetime.combine(data_inicio, datetime.min.time())
        fim = datetime.combine(hoje, datetime.max.time())

        total_chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.data_criacao >= inicio,
            Chamado.data_criacao <= fim
        ).count()

        return jsonify({
            "status": "success",
            "total_chamados": total_chamados
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@insights_bp.route('/ChamadosSuporte/finalizado', methods=['POST'])
def listar_chamados_finalizado():
    try:
        dias = int(request.json.get("dias", 1))  # padrão: 1 dia
        hoje = datetime.now().date()
        data_inicio = hoje - timedelta(days=dias)

        inicio = datetime.combine(data_inicio, datetime.min.time())
        fim = datetime.combine(hoje, datetime.max.time())

        total_chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.data_finalizacao != None,
            Chamado.data_finalizacao >= inicio,
            Chamado.data_finalizacao <= fim
        ).count()

        return jsonify({
            "status": "success",
            "total_chamados": total_chamados
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@insights_bp.route('/sla', methods=['POST'])
def sla_insights():
    try:
        data = request.get_json()
        dias = int(data.get('dias', 1)) 
        hoje = datetime.now()
        data_inicio = hoje - timedelta(days=dias - 1)

        # Filtro: status diferente de cancelado e dentro do período
        chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.data_criacao >= datetime.combine(data_inicio.date(), datetime.min.time()),
            Chamado.data_criacao <= datetime.combine(hoje.date(), datetime.max.time())
        ).all()

        # Filtra os com SLA expirado
        expirados_atendimento = sum(1 for c in chamados if c.sla_atendimento == 'S')
        expirados_resolucao = sum(1 for c in chamados if c.sla_resolucao == 'S')
        chamados_atendimento_prazo = sum(1 for c in chamados if c.sla_atendimento == 'N')
        chamados_finalizado_prazo = sum(1 for c in chamados if c.sla_resolucao == 'N')

        chamados_prazo = [
            c for c in chamados if c.sla_atendimento == 'N' or c.sla_resolucao == 'N'
        ]

        # Lista completa de expirados para retornar os códigos
        chamados_expirados = [
            c for c in chamados if c.sla_atendimento == 'S' or c.sla_resolucao == 'S'
        ]

        total_chamados = len(chamados)

        percentual_atendimento = round((expirados_atendimento / total_chamados) * 100, 2) if total_chamados else 0
        percentual_resolucao = round((expirados_resolucao / total_chamados) * 100, 2) if total_chamados else 0

        percentual_prazo_atendimento = round((chamados_atendimento_prazo/total_chamados) * 100, 2) if total_chamados else 0
        percentual_prazo_resolucao = round((chamados_finalizado_prazo/total_chamados) * 100, 2) if total_chamados else 0

        return jsonify({
            "status": "success",
            "total_chamados": total_chamados,
            "prazo_atendimento": chamados_atendimento_prazo,
            "percentual_prazo_atendimento" : percentual_prazo_atendimento,
            "percentual_prazo_resolucao": percentual_prazo_resolucao,
            "expirados_atendimento": expirados_atendimento,
            "prazos_resolucao": chamados_finalizado_prazo,
            "expirados_resolucao": expirados_resolucao,
            "percentual_atendimento": percentual_atendimento,
            "percentual_resolucao": percentual_resolucao,
            "codigos_atendimento": [c.cod_chamado for c in chamados_expirados if c.sla_atendimento == 'S'],
            "codigos_resolucao": [c.cod_chamado for c in chamados_expirados if c.sla_resolucao == 'S'],
            "codigos_prazo_atendimento": [c.cod_chamado for c in chamados if c.sla_atendimento == 'N'],
            "codigos_prazo_resolucao": [c.cod_chamado for c in chamados if c.sla_resolucao == 'N']
        })


    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Rota traz os chamados abertos atualmente
@insights_bp.route('/ChamadosEmAbertoSuporte', methods=['POST'])
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