from app import app
from modules.delgrande.relatorios.utils import processar_e_armazenar_performance, processar_e_armazenar_performance_vyrtos

with app.app_context():
    print("Tarefa em execução!")
    processar_e_armazenar_performance()