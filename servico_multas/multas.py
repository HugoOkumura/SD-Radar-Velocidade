from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from leitura_pb2_grpc import add_LeituraServiceServicer_to_server , LeituraServiceServicer
import leitura_pb2 
import grpc

from http.server import BaseHTTPRequestHandler, HTTPServer

from concurrent import futures
from threading import Thread
import os
import logging
import ssl
import json
import hashlib
import base64

from datetime import datetime, timezone
from google.protobuf.timestamp_pb2 import Timestamp

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

SERVICE_PORT = os.getenv('SERVICO_LEITURAS_PORT')
MONGODB_URI = "mongodb+srv://admin:admin@sd.wrdeptn.mongodb.net/?retryWrites=true&w=majority&appName=SD"

class MultasServico(LeituraServiceServicer):
    
    def __init__(self):
        self.mongo = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
        self.db = self.mongo['SD_Projeto']
        self.multa_db = self.db['Multas']
        self.usuario_db = self.db['Usuarios']

    def GerenciaLeituras(self, request, context):
        try:
            logging.info(request)
            usuario = self.usuario_db.find_one({"placa":request.placa})
            usuario = self.doc_to_usuario(usuario)

            data = Timestamp(request.data).ToDatetime()

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

            multa_gerada = self.multa_db.insert_one(multa_documento).inserted_id

            logging.info(f"Multa registrada: {multa_gerada}")


            return leitura_pb2.Resposta(
                user=leitura_pb2.Usuario(
                    id=usuario['_id'],
                    nome=usuario['nome'],
                    placa=usuario['placa']
                ),
                sucesso=True
            )

        except Exception as e:
            logging.error(f"Falha ao registrar a multa: {e}")
            return leitura_pb2.Resposta(
                user=None,
                sucesso=False
            )

    def doc_to_usuario(self, doc):
        return leitura_pb2.Usuario(
            id=str(doc.get("_id","")),
            nome=doc.get("nome",""),
            placa=doc.get("placa","")
        )


class MultasAPI(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.mongo = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
        self.db = self.mongo['SD_Projeto']
        self.multas = self.db['Multas']
        self.usuarios = self.db['Usuario']
        super().__init__(*args, **kwargs)

    def _authenticate(self, nome, senha):
        usuario = self.usuarios.find_one({'nome':nome})
        if not usuario:
            return None
        
        salt = os.getenv('DB_SALT')
        senha512 = hashlib.pbkdf2_hmac('sha512',senha.encode('utf-8'), salt,) 

        if senha512 == base64.b64decode(usuario['senha']):
            return usuario
        return None
    
    def _get_credenciais(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Basic '):
            return None
        
        auth_decoded = base64.b64decode(auth_header[6:].decode('utf-8'))
        return auth_decoded.split(':',1)

    def do_GET(self):
        if self.path == '/multas':
            credenciais = self._get_credenciais()
        
            if not credenciais:
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm="Multas API')
                self.end_headers()
                return
        
            nome, senha = credenciais
            usuario = self._authenticate(nome, senha)
            if not usuario:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b'Invalid credentials')
                return
            
            # Buscar multas apenas para a placa do usuário
            fines = list(self.multas.find(
                {'placa': usuario['placa']} 
            ))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(fines).encode())
        else:
            self.send_response(404)
            self.end_headers()           


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

def ApiServe():
    handler = lambda *args: MultasAPI(*args)
    api = HTTPServer(('127.0.0.1', 5000),handler)
    logging.info("API de multas foi inicializado")
    api.serve_forever()


if __name__ == "__main__":
    startLog()
    grpc_thread = Thread(target=serve_grpc)
    grpc_thread.start()

    ApiServe()