from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required


home_bp = Blueprint('home_bp', __name__)

@home_bp.route('/home', methods=['GET'])
def render_home():
    return render_template('home.html')

@home_bp.route('/', methods=['GET'])
def render_login():
    return render_template('login.html')

