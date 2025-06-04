from flask import Blueprint, jsonify, request
from modules.delgrande.filas import utils
from modules.delgrande.auth.utils import authenticate 
from application.models import Fila, FilaVyrtus, db
from settings.endpoints import CREDENTIALS
from datetime import datetime


filas_bp = Blueprint('filas_bp', __name__, url_prefix='/dashboard/call')


# SUPORTE
@filas_bp.route('/v2/report/queue_status', methods=['POST'])
def importar_status_fila():
    id = 1
    try:
        # 1. Autenticar
        username = CREDENTIALS['username']
        password = CREDENTIALS['password']
        token = authenticate(username, password)

        # 2. Buscar dados da fila
        response = utils.get_filas(token, id)
        status = response.get("result", {}).get("status", {})

        if not status:
            return jsonify({"status": "error", "message": "Nenhuma informação encontrada para a fila"}), 204

        # 3. Extrair e processar dados
        chamadas_completadas = status.get("completed", 0)
        chamadas_abandonadas = status.get("abandoned", 0)
        transbordo = status.get("exitwithkey", 0)
        chamadas_recebidas = chamadas_completadas + chamadas_abandonadas + transbordo

        # 4. Limpar e salvar no banco
        with db.session.begin():
            db.session.query(Fila).delete()
            nova_fila = Fila(
                numero=status.get("number"),
                nome=status.get("name"),
                tipo=status.get("type"),
                chamadas_completadas=chamadas_completadas,
                chamadas_abandonadas=chamadas_abandonadas,
                transbordo=transbordo,
                chamadas_recebidas=chamadas_recebidas,
                tempo_espera=status.get("holdtime"),
                tempo_fala=status.get("talktime"),
                nivel_servico=status.get("servicelevelperf"),
                data=datetime.now()
            )
            db.session.add(nova_fila)

        # 5. Retorno formatado para o front
        return jsonify({
            "status": "success",
            "data": [{
                "fila": status.get("name"),
                "chamadas_recebidas": chamadas_recebidas,
                "chamadas_completadas": chamadas_completadas,
                "chamadas_abandonadas": chamadas_abandonadas,
                "transbordo": transbordo,
                "nivel_servico": status.get("servicelevelperf")
            }]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Erro ao importar status da fila.",
            "details": str(e)
        }), 500

# VYRTUS
@filas_bp.route('/v2/report/queue_status_vyrtus', methods=['POST'])
def importar_status_fila_vyrtus():
    id = 10
    try:
        # 1. Autenticar
        username = CREDENTIALS['username']
        password = CREDENTIALS['password']
        token = authenticate(username, password)

        # 2. Buscar dados da fila
        response = utils.get_filas(token, id)
        status = response.get("result", {}).get("status", {})

        if not status:
            return jsonify({"status": "error", "message": "Nenhuma informação encontrada para a fila"}), 204

        # 3. Extrair e processar dados
        chamadas_completadas = status.get("completed", 0)
        chamadas_abandonadas = status.get("abandoned", 0)
        transbordo = status.get("exitwithkey", 0)
        chamadas_recebidas = chamadas_completadas + chamadas_abandonadas + transbordo

        # 4. Limpar e salvar no banco
        with db.session.begin():
            db.session.query(FilaVyrtus).delete()
            nova_fila = FilaVyrtus(
                numero=status.get("number"),
                nome=status.get("name"),
                tipo=status.get("type"),
                chamadas_completadas=chamadas_completadas,
                chamadas_abandonadas=chamadas_abandonadas,
                transbordo=transbordo,
                chamadas_recebidas=chamadas_recebidas,
                tempo_espera=status.get("holdtime"),
                tempo_fala=status.get("talktime"),
                nivel_servico=status.get("servicelevelperf"),
                data=datetime.now()
            )
            db.session.add(nova_fila)

        # 5. Retorno formatado para o front
        return jsonify({
            "status": "success",
            "data": [{
                "fila": status.get("name"),
                "chamadas_recebidas": chamadas_recebidas,
                "chamadas_completadas": chamadas_completadas,
                "chamadas_abandonadas": chamadas_abandonadas,
                "transbordo": transbordo,
                "nivel_servico": status.get("servicelevelperf")
            }]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Erro ao importar status da fila.",
            "details": str(e)
        }), 500


@filas_bp.route('/v2/report/agents_status', methods=['POST'])
def agentes_online_status():
    id = 1  # ou receber via parâmetro, se quiser
    try:
        username = CREDENTIALS['username']
        password = CREDENTIALS['password']
        token = authenticate(username, password)

        response = utils.get_filas(token, id)
        status = response.get("result", {}).get("status", {})

        if not status:
            return jsonify({"status": "error", "message": "Nenhuma informação encontrada para a fila"}), 204

        members = status.get("members", [])
        if not members:
            return jsonify({"status": "success", "members": [], "message": "Nenhum agente online encontrado."})

        # Processar membros para adicionar informações de tempo online e pausa
        agentes = []
        now_timestamp = int(datetime.now().timestamp())

        for m in members:
            # Calcular tempo online em segundos (diferença entre agora e entryTime)
            tempo_online_segundos = now_timestamp - m.get("entryTime", now_timestamp)

            # Exemplo: Se "penalty" > 0 considerar que está em pausa, e se tiver uma pausa (fictícia)
            em_pausa = m.get("penalty", 0) > 0
            
            # Para o motivo da pausa (exemplo), se não tem no JSON real, colocar "Indefinido"
            motivo_pausa = m.get("pause_reason", "Indefinido") if em_pausa else None

            agente = {
                "agentNumber": m.get("agentNumber"),
                "tempo_online": tempo_online_segundos,
                "em_pausa": em_pausa,
                "motivo_pausa": motivo_pausa
            }
            agentes.append(agente)

        return jsonify({
            "status": "success",
            "members": agentes
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao obter status dos agentes.",
            "details": str(e)
        }), 500
