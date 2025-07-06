import grpc
import paho.mqtt.client as mqtt
import os
import json
import logging
import threading
from queue import Queue
from db_store import LeiturasManager
import leitura_pb2
import leitura_pb2_grpc
from datetime import datetime, timezone
from dateutil import parser
from google.protobuf.timestamp_pb2 import Timestamp
from numpy import int32
'''
Nome: Hugo Naoki Sonoda Okumura
Criado: 23/06/2025
Última atualização: 29/06/2025
 # Este código implementa as funçonalidades de receber as mensagens enviadas para o MQTT Broker.
 # Aqui, o código se inscreve no tópico das leituras de velocidade e irá armazenar num banco de dados MongoDB. 
 # Mais detalhes sobre o gerenciamento do banco de dados está no arquivo db_store.py
'''

# pega as variáeis de ambiente do docker
MQTT_BROKER = os.getenv('MOSQUITTO_HOST')
MQTT_PORT = int(os.getenv('MOSQUITTO_PORT'))
MQTT_TOPIC = os.getenv('MOSQUITTO_TOPIC')
MULTAS_SERVER = os.getenv('MULTAS_SERVER')
MULTAS_PORT = int(os.getenv('MULTAS_PORT'))

# Configurações do Log do sistema
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

'''
Classe que irá gerenciar as leituras recebidas pelo Broker MQTT
'''
class ServicoLeitura():
    def __init__(self):
        
        # buffer de leituras
        # self.leituras = deque(maxlen=50)
        self.leituras = Queue(maxsize=100)

        # inicialização da conexão com o banco
        self.mongo = LeiturasManager()

        logging.info(f"Serviço de Leituras conectou-se ao MongoDB")
        '''
        Configuração do consumer MQTT
        '''
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"Servico_Leitura",
            clean_session=False
        )
        self.client.enable_logger()
        self.client.on_connect = self._on_connect
        self.client.on_subscribe = self._on_subscribe
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self.receive_thread = threading.Thread(target=self.thread_recebe, daemon=True)
        self.stop = threading.Event()

        logging.info(f"Serviço de Leituras Iniciado")

        self.connect()

    '''
    Definição dos Callbacks.
     # Os callbacks servem para definir funcionalidades em resposta a certos eventos entre a comunicação 
     # entre processo e serviço.
    '''

    # Callback de conexão com o broker
    def _on_connect(self, client, userdata, connect_flags, reason_code, properties):
        if reason_code.is_failure:
            logging.error(f"Serviço de Leituras falhou em conectar ao MQTT broker: {reason_code}")
        else:
            logging.info(f"Serviço de Leituras conectou-se ao MQTT broker")
            self.client.subscribe(MQTT_TOPIC)

    # Callback de inscrição com um tópico do broker
    def _on_subscribe(self,client, userdata, mid, reason_code_list, properties):
        if reason_code_list[0].is_failure:
            logging.error(f"Serviço de Leituras falhou no subscribe: {reason_code_list[0]}")
        else:
            logging.info(f"Serviço de Leituras inscreveu no Broker: {reason_code_list[0].value}")

    # Callback de recebimento de mensagens no tópico inscrito
    def _on_message(self, client, userdata, message):
        logging.info(f"Serviço de Leituras recebeu uma leitura")
        message = json.loads(message.payload.decode())
        message['data'] = parser.isoparse(message['data'])
        self.leituras.put_nowait(message)

    # Callback de desconecção ao broker
    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        logging.info(f"Serviço de Leituras se desconectou do broker: {reason_code}")

    '''
    Métodos do serviço
    '''

    '''
    Rotina de inserir as leituras para o banco de dados
    '''
    def run(self):

        threading.Thread(target=self.send_to_servico_multas, daemon=True).start()

        while True:
            if not self.leituras.empty():
                leitura = self.leituras.get()

                if self.mongo.insert(leitura):
                    logging.info(f"Serviço de Leituras inseriu uma leitura no banco")
                else:
                    logging.error(f"Serviço de Leituras falhou em inserir uma leitura no banco")
                    self.leituras.put_nowait(leitura)

                self.leituras.task_done()

    '''
    Stub gRPC com conexão segura
    '''
    def create_grpc_connection(self):
        with open('ca-cert.pem','rb') as certif:
            trusted_certs = certif.read()

            credenciais = grpc.ssl_channel_credentials(
                root_certificates=trusted_certs,
            )
            options = [('grpc.ssl_target_name_override', 'servico_multas')]
            return grpc.secure_channel(
                f"{MULTAS_SERVER}:{MULTAS_PORT}",
                credenciais,
                options=options
            )
        
    '''
    Thread que irá enviar Todas as leituras que são marcadas como infrações para o serviço de multas
    '''
    def send_to_servico_multas(self):
        while True:
            try:
                infracoes = self.mongo.retrieve_infracoes()

                for infracao in infracoes:
                    with self.create_grpc_connection() as grpc_channel:
                        stub = leitura_pb2_grpc.LeituraServiceStub(grpc_channel)

                        time = Timestamp()
                        time.FromDatetime(infracao['data'])
                        # logging.info(Timestamp().FromDatetime(infracao['data']))

                        response = stub.GerenciaLeituras(leitura_pb2.Leitura(
                            limite = infracao['limite'],
                            data = time,
                            velocidade = float(infracao['velocidade']),
                            placa = str(infracao['placa'])
                        ))

                        if response.sucesso == True:
                            logging.info("Serviço de Leituras enviou uma infração para o Serviço de Multas")
                            self.mongo.change_status(infracao)
                        else:
                            raise Exception(f"Serviço de multas rejeitou o envio da multa")
                        
            except Exception as e:
                logging.error(f"Serviço de Leituras falhou em enviar infração: {e}")

    '''
    Método que faz a rotina de conexão e inicia a thread que inicia o loop de recebimento de mensagens
    '''
    def connect(self):
        try:
            self.client.connect(
                host=MQTT_BROKER,
                port=MQTT_PORT
            )
            self.receive_thread.start()
        except Exception as e:
            logging.error(f"Serviço de Leituras: erro ao conectar - {e}")

    '''
    Thread que irá receber todas as mensagens do broker
    '''
    def thread_recebe(self):
        print("THREAD")
        # O loop de network irá ficar em execução eternamente para receber as mensagens
        self.client.loop_forever()


def main():
    os.makedirs("./logs", exist_ok=True)
    open("logs/logs.log","a+").close()
    startLog()
    try:
        servico_leituras = ServicoLeitura()
        servico_leituras.run()
    except KeyboardInterrupt:
        logging.info(f"Serviço de leituras foi encerrado")


if __name__ == "__main__":
    main()
