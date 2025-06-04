import requests, json
import settings.endpoints as endpoints
from urllib.parse import urlencode
from urllib.parse import urlencode
import json

def get_relatorio(token, params):
    base_url = endpoints.REPORT

    # Montagem manual da URL com os parâmetros esperados pela API
    url = (
        f"{base_url}"
        f"?initial_date={params.initial_date}"
        f"&initial_hour={params.initial_hour}"
        f"&final_date={params.final_date}"
        f"&final_hour={params.final_hour}"
        f"&fixed={params.fixed}"
        f"&week={params.week}"
        f"&options={params.options}"
        f"&queues={params.queues}"
        f"&agents={params.agents}"
        f"&transfer_display={params.transfer_display}"
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status_code": getattr(e.response, "status_code", 500),
            "url": url
        }


def get_relatorio_login_logoff(token, params):
    base_url = endpoints.LOGIN_LOGOFF

    # Serializar corretamente a lista de semana e agentes
    week = params.week.replace(" ", "")  # "1,2,3,4,5"
    agents = params.agents.replace(" ", "")  # "1001,1002"

    # Converter string JSON do options para URL-encoded (com segurança)
    try:
        options = json.loads(params.options)
        options_encoded = json.dumps(options)
    except Exception:
        options_encoded = "{}"

    # Montar a URL manualmente
    url = (
        f"{base_url}"
        f"?initial_date={params.initial_date}"
        f"&initial_hour={params.initial_hour}"
        f"&final_date={params.final_date}"
        f"&final_hour={params.final_hour}"
        f"&fixed={params.fixed}"
        f"&week={week}"
        f"&options={options_encoded}"
        f"&agents={agents}"
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status_code": getattr(e.response, "status_code", 500),
            "url": url
        }


def get_chamada_saida(token, params):
    base_url = endpoints.CHAMADA_SAIDA

    # Serializar corretamente a lista de semana e agentes
    week = params.week.replace(" ", "")
    agents = params.agents.replace(" ", "")

    # Converter string JSON do options para URL-encoded (com segurança)
    try:
        options = json.loads(params.options)
        options_encoded = json.dumps(options)
    except Exception:
        options_encoded = "{}"

    # Montar a URL manualmente
    url = (
        f"{base_url}"
        f"?initial_date={params.initial_date}"
        f"&initial_hour={params.initial_hour}"
        f"&final_date={params.final_date}"
        f"&final_hour={params.final_hour}"
        f"&fixed={params.fixed}"
        f"&week={week}"
        f"&conf={params.conf}"
        f"&options={options_encoded}"
        f"&agents={agents}"
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status_code": getattr(e.response, "status_code", 500),
            "url": url
        }


def atendentePerformance(token, params):
    base_url = endpoints.PERFORMANCE_ATENDENTES

    query_params = {
        "initial_date": params.initial_date,
        "initial_hour": params.initial_hour,
        "final_date": params.final_date,
        "final_hour": params.final_hour,
        "week": params.week,
        "conf": params.conf,
        "agents": params.agents,
        "queues": params.queues,
        "options": params.options
    }

    # Transforma dicionários em strings JSON antes de passar para requests
    for key in ["options", "conf", "agents", "queues"]:
        if isinstance(query_params[key], (dict, list)):
            query_params[key] = json.dumps(query_params[key])

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(base_url, headers=headers, params=query_params)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status_code": getattr(e.response, "status_code", 500),
            "url": base_url
        }
