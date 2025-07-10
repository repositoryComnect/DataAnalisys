import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_apscheduler import APScheduler
from werkzeug.security import generate_password_hash

from application.models import db, User
from modules.home.routes import home_bp
from modules.login.routes import login_bp
from modules.deskmanager.authenticate.routes import auth_bp
from modules.delgrande.filas.routes import filas_bp
from modules.delgrande.relatorios.routes import relatorio_bp
from modules.deskmanager.auth.routes import auth_desk_bp
from modules.deskmanager.dashboard.routes import dashboard_bp
from modules.admin.routes import admin_bp
from modules.delgrande.operadores.routes import operadores_bp
from modules.insights.routes import insights_bp
from modules.relatorios.routes import relatorios_bp
from modules.delgrande.relatorios.utils import (
    processar_e_armazenar_performance,
    processar_e_armazenar_performance_vyrtos,
    importar_chamados,
    processar_e_armazenar_performance_incremental,
    processar_e_armazenar_performance_vyrtos_incremental,
    importar_pSatisfacao
)

# ----------------- LOGGING CONFIG -----------------
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')

handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

app_logger = logging.getLogger()
app_logger.setLevel(logging.INFO)
app_logger.addHandler(handler)
# ---------------------------------------------------

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:%40Slink1205@localhost/data'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())

# Register blueprints
app.register_blueprint(home_bp)
app.register_blueprint(login_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(filas_bp)
app.register_blueprint(relatorio_bp)
app.register_blueprint(auth_desk_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(operadores_bp)
app.register_blueprint(insights_bp)
app.register_blueprint(relatorios_bp)

# Init extensions
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Scheduled task functions
def tarefa_horaria_processar_performance():
    with app.app_context():
        try:
            logging.info("[AGENDADO] Iniciando coleta e armazenamento de performance padrão...")
            resultado1 = processar_e_armazenar_performance_incremental()
            logging.info(f"[AGENDADO] Resultado padrão: {resultado1}")
        except Exception as e:
            logging.error(f"[AGENDADO] Erro ao importar performance. ")
        
def tarefa_horaria_processar_performance_vyrtos():
    with app.app_context():
        try:
            logging.info("[AGENDADO] Iniciando coleta e armazenamento de performance Vyrtos...")
            resultado2 = processar_e_armazenar_performance_vyrtos_incremental(incremental=True)
            logging.info(f"[AGENDADO] Resultado Vyrtos: {resultado2}")
        except Exception as e:
            logging.error(f"[AGENDADO] Erro ao importar performance. ")

def tarefa_importar_chamados():
    with app.app_context():
        try:
            total = importar_chamados()
            logging.info(f"[AGENDADO] {total} chamados importados com sucesso.")
        except Exception as e:
            logging.error(f"[AGENDADO] Erro ao importar chamados: {e}")

def tarefa_importar_psatisfacao():
     with app.app_context():
        try:
            total = importar_pSatisfacao()
            logging.info(f"[AGENDADO] {total} chamados importados com sucesso.")
        except Exception as e:
            logging.error(f"[AGENDADO] Erro ao importar chamados: {e}")

# APScheduler
scheduler = APScheduler()

with app.app_context():
    db.create_all()

    # Create admin user if missing
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('admin123'), is_admin=True)
        db.session.add(admin)
        db.session.commit()
        logging.info("Usuário admin criado com sucesso.")

    scheduler.init_app(app)

    scheduler.add_job(
        id='job_processa_performance_horaria',
        func=tarefa_horaria_processar_performance,
        trigger='interval',
        minutes=5
    )

    scheduler.add_job(
        id='job_processa_performance_horaria_vyrtos',
        func=tarefa_horaria_processar_performance_vyrtos,
        trigger='interval',
        minutes=5
    )

    scheduler.add_job(
        id='job_importar_chamados',
        func=tarefa_importar_chamados,
        trigger='interval',
        minutes=5
    )

    scheduler.add_job(
        id='job_importar_psatisfacao',
        func=tarefa_importar_psatisfacao,
        trigger='interval',
        minutes=5
    )

    scheduler.start()
    logging.info("Tarefas agendadas iniciadas.")

# Debug logs do APScheduler
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

# Run app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=False)
