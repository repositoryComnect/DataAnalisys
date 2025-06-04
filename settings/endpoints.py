
# Endpoints globais DelGrande

AUTHENTICATE = "http://192.168.10.35:9444/v2/auth"

QUEUES = 'http://192.168.10.35:9444/v2/queues/'

REPORT = 'http://192.168.10.35:9444/v2/report/call_detailing'

LOGIN_LOGOFF = 'http://192.168.10.35:9444/v2/report/login_logoff'

CHAMADA_SAIDA = 'http://192.168.10.35:9444/v2/report/call_detailing_outgoing'

PERFORMANCE_ATENDENTES = 'http://192.168.10.35:9444/v2/report/attendants_performance'

CREDENTIALS = {
    'username' : 'lolegario',
    'password' : '@Telecom01'
}

# Endpoints globais Desk Manager

CREDENTIALS_DESK = {
    'Authorization' : '53bbaf715b107908b827f648ac9853278cff40ed',
    'PublicKey' : '1557725d2f04eabdfbc46fb7e589389a2ff7c0da'
}



AUTHENTICATE_DESK = 'https://api.desk.ms/Login/autenticar'

LISTACHAMADOS = 'https://api.desk.ms/Chamados/lista'

LISTA_CHAMADOS_SUPORTE = 'https://api.desk.ms/ChamadosSuporte/lista'