import grpc
import paho.mqtt.client as mqtt
import os
import json
import logging
import threading
from queue import Queue
from db_store import LeiturasManager

'''
Nome: Hugo Naoki Sonoda Okumura
Criado: 23/06/2025
Última atualização: 29/06/2025
 # Este código implementa as funçonalidades de receber as mensagens enviadas para o MQTT Broker.
 # Aqui, o código se inscreve no tópico das leituras de velocidade e irá armazenar num banco de dados MongoDB. 
 # Mais detalhes sobre o gerenciamento do banco de dados está no arquivo db_store.py
'''

MQTT_BROKER = os.getenv('MOSQUITTO_HOST')
MQTT_PORT = int(os.getenv('MOSQUITTO_PORT'))
MQTT_TOPIC = os.getenv('MOSQUITTO_TOPIC')

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
        try:
            self.mongo.admin.command('ping')
        except Exception as e:
            logging.error(f"Serviço de Leituras falhou ao conectar ao MongoDB")

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
        print(message)
        self.leituras.put_nowait(message)

    # Callback de desconecção ao broker
    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        logging.info(f"Serviço de Leituras se desconectou do broker: {reason_code}")

    '''
    Métodos do serviço
    '''
    def run(self):
        while True:
            if not self.leituras.empty():
                leitura = self.leituras.get()

                if self.mongo.insert(leitura):
                    logging.info(f"Serviço de Leituras inseriu uma leitura no banco")
                else:
                    logging.error(f"Serviço de Leituras falhou em inserir uma leitura no banco")
                    self.leituras.put_nowait(leitura)

                self.leituras.task_done()

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
