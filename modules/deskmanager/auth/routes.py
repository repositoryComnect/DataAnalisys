from flask import Blueprint, jsonify, request, render_template

auth_desk_bp = Blueprint('auth_desk_bp', __name__)

@auth_desk_bp.route('/chamados/lista', methods=['POST'])
def chamados_lista():
    data = request.get_json()

    pesquisa = data.get('Pesquisa')
    codSolicitante = data.get('CodSolicitante')
    ordem = data.get('Ordem')



    return