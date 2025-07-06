from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import AutoReconnect
from leitura_pb2_grpc import add_LeituraServiceServicer_to_server , LeituraServiceServicer
import leitura_pb2 
import grpc
from concurrent import futures
from threading import Thread
import os
import logging
import time
import json
import hashlib
import base64
from datetime import datetime, timezone
from google.protobuf.timestamp_pb2 import Timestamp
from flask import Flask, request, jsonify, make_response
from flask_httpauth import HTTPBasicAuth

'''
Nome: Hugo Naoki Sonoda Okumura
Criado: 01/07/2025
Última atualização: 06/07/2025
 # Este código implementa o serviço de multas e a API que o aplicativo web que o usuário irá utilizar para
 # acessar suas multas.
 # Aqui, é inicializado um servidor gRPC que irá receber leituras de infrações de velocidade e irá procurar
 # qual usuário que cometeu a infração a partir da placa lida pelos dispositivos IoT. Ao encontrar quem foi o 
 # responsável, irá armazenar em banco de dados MongoDB. 
'''

# inicializa e configura o logger
def startLog():
    logging.basicConfig(
        level=logging.INFO,
        format="{asctime} - {levelname} - {message}",
        datefmt="%d-%m-%Y %H:%M",
        style="{",
        filename="./logs/logs.log",
        encoding="utf-8",
        filemode="a"
    )

# Porta que o grpc irá ser inicializado 
SERVICE_PORT = os.getenv('MULTAS_GRPC_PORT')
# URI do banco de dados MongoDB Atlas
MONGODB_URI = os.getenv('MONGO_URI')


'''
Inicializa a conexão com o banco de dados e seleciona as coleções utilizadas
'''
mongo = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
db = mongo['SD_Projeto']
multas_db = db['Multas']
usuario_db = db['Usuarios']


'''
Class que irá gerenciar a conexão do gRPC com o serviço de leituras
'''
class MultasServico(LeituraServiceServicer):
    def __init__(self):
        logging.info(f"Serviço de Multas conectou-se ao MongoDB")


    '''
    Método princiapl do servidor gRPC. Aqui é onde será recebida as leituras de velocidade e armazenados no MongoDB.
    Retorna para o serviço de Leituras um objeto de Usuario que possui a placa do veículo infrator. 
    '''
    def GerenciaLeituras(self, request, context):
        try:
            # usuario = self.usuario_db.find_one({"placa":request.placa})
            usuario = usuario_db.find_one({"placa":request.placa})
            usuario = self.doc_to_usuario(usuario)

            data = request.data.ToDatetime()

            multa_documento = {
                "limite":request.limite,
                "data":data,
                "velocidade":request.velocidade,
                "paga":False,
                "usuario":{
                    "user_id":usuario.id,
                    "user_placa":usuario.placa
                }
            }

            # multa_gerada = self.multa_db.insert_one(multa_documento).inserted_id
            multa_gerada = multas_db.insert_one(multa_documento).inserted_id

            logging.info(f"Multa registrada: {multa_gerada}")


            return leitura_pb2.Resposta(
                user=usuario,
                sucesso=True
            )

        except Exception as e:
            logging.error(f"Falha ao registrar a multa: {e}")
            return leitura_pb2.Resposta(
                user=None,
                sucesso=False
            )

    '''
    Método de converção de Leitura para um documento inserível no banco
    '''
    def doc_to_usuario(self, doc):
        return leitura_pb2.Usuario(
            id=str(doc.get("_id","")),
            nome=doc.get("nome",""),
            placa=doc.get("placa","")
        )

'''
Configuração da API REST de Multas usando Flask
'''
app = Flask(__name__)
auth = HTTPBasicAuth()

'''
Método para verificar as credenciais de autenticação 
'''
@auth.verify_password
def verify_password(username,password):
    try:
        usuario = usuario_db.find_one({'nome':username})
        if not usuario:
            return None
        
        salt = os.getenv('DB_SALT').encode('utf-8')
        senha_hash = hashlib.pbkdf2_hmac(
            'sha512',
            password.encode('utf-8'),
            salt,
            100000
        )

        if base64.b64encode(senha_hash).decode('utf-8') == usuario['senha']:
            return username
        return None
    except Exception as e:
        logging.error(f"Erro na autenticação: {e}")
        return None

'''
Endpoint que lista todas as multas do usuário autenticado
'''
@app.route('/multas', methods=['GET'])
@auth.login_required
def get_multas():
    try:
        usuario = usuario_db.find_one({'nome': auth.current_user()})
        if not usuario:
            return jsonify({'error':"Usuário não encontrado"}), 404
        
        multas = list(multas_db.find(
            {
            'usuario.user_id': str(usuario['_id']),
            'usuario.user_placa': usuario['placa']
            }
        ))

        for multa in multas:
            multa['_id'] = str(multa['_id'])
            multa['data'] = multa['data'].isoformat()
            multa['paga'] = 'Paga' if multa['paga'] else 'Pendente'

        return jsonify(multas)
    except Exception as e:
        logging.error(f"Erro ao buscar multas: {e}")
        return jsonify({'error':'Erro interno'}), 500

'''
Endpoint de validação de login
'''
@app.route('/validate_login', methods=['GET'])
@auth.login_required
def validate_login():
    try:
        usuario = usuario_db.find_one({'nome': auth.current_user()})
        if not usuario:
            return jsonify({'valid': False, 'error': 'Usuário não encontrado'}), 200
        
        return jsonify({
            'valid': True,
            'placa': usuario.get('placa', ''),
            'nome': usuario.get('nome', '')
        }), 200
    except Exception as e:
        logging.error(f"Erro na validação de login: {e}")
        return jsonify({'valid': False, 'error': 'Erro interno'}), 200


'''
Thread que irá configurar e inicializar o servidor gRPC
'''
def serve_grpc():
    with open('server-cert.pem', 'rb') as f:
        certificate = f.read()
    with open('server-key.pem', 'rb') as f:
        private_key = f.read()


    server_credenciais = grpc.ssl_server_credentials(
        private_key_certificate_chain_pairs=[(private_key,certificate)],
        root_certificates=None,
        require_client_auth=False
    )
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_LeituraServiceServicer_to_server(MultasServico(), server)

    server.add_secure_port(f"[::]:{SERVICE_PORT}", server_credenciais)

    logging.info("Serviço de Multas inicializado")
    server.start()
    server.wait_for_termination()
    logging.info("Serviço de Multas finalizado")


if __name__ == "__main__":
    startLog()
    grpc_thread = Thread(target=serve_grpc)
    grpc_thread.start()
    print('ok')

    app.run(host='0.0.0.0', port=5000)