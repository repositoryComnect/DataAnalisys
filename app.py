from flask import Flask, jsonify, request, redirect, Blueprint
from modules.home.routes import home_bp
from modules.delgrande.filas.routes import filas_bp
from modules.delgrande.relatorios.routes import relatorio_bp
from modules.deskmanager.auth.routes import auth_desk_bp
from modules.login.routes import login_bp
from modules.deskmanager.dashboard.routes import dashboard_bp
from modules.deskmanager.authenticate.routes import auth_bp
from modules.admin.routes import admin_bp
from modules.delgrande.operadores.routes import operadores_bp
from flask_login import LoginManager
from flask_migrate import Migrate
from application.models import db, User
from werkzeug.security import generate_password_hash

import os

app = Flask(__name__)

app.register_blueprint(home_bp)
app.register_blueprint(login_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(filas_bp)
app.register_blueprint(relatorio_bp)
app.register_blueprint(auth_desk_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(operadores_bp)
#app.register_blueprint(auth_desk_manager_bp)


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:%40Slink1205@localhost/data'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

# Inicializa o db com o app
db.init_app(app)
migrate = Migrate(app, db)

# Inicialização do LoginManager
login_manager = LoginManager(app)

# Configuração do LoginManager
login_manager.login_view = 'login.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Criação do banco e usuário admin
with app.app_context():
    db.create_all()
    
    # Verifica se o usuário admin já existe
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()


if __name__ == '__main__':
        app.run(host='0.0.0.0', port=9000, debug=True)
