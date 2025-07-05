import random
import time
import paho.mqtt.client as mqtt
import json
import os
import threading
import logging
from collections import deque  
from dataclasses import dataclass
from datetime import datetime, timezone

'''
Nome: Hugo Naoki Sonoda Okumura
Criado: 10/06/2025
Última atualização: 29/06/2025
 # Este código implementa o simulador de dispositivos IoT.
 # Aqui, irá criar threads que serão os processos dos dispositivos que irão gerar leituras aleatórias de velocidade e
 # cada dispositivo irá criar outra thread que irá enviar todos as leituras para o mqtt broker.
'''

# pega as variáeis de ambiente do docker
MQTT_BROKER = os.getenv('MOSQUITTO_HOST')
MQTT_PORT = int(os.getenv('MOSQUITTO_PORT'))
MQTT_TOPIC = os.getenv('MOSQUITTO_TOPIC')

# Lista de velocidades
LIMITES = [40,60,80,100,110]

# Lista de placas de automóveis
PLACAS= ["ABC1D23", "BRA2E19", "FGH5J67",
         "KLM9N45", "OPQ8R21", "STU3V90",
         "WXY7Z34", "JKL4M56", "DEF6G78",
         "MNO1P29"
        ]

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
Classe que modela o formato da leitura.
'''
@dataclass
class LeituraFormato:
    id_dispositivo: str
    limite: int
    data: time
    velocidade: int
    placa: str

'''
Classe que irá transmitir os sinais de dispositivos IoT. Cria uma thread que 
irá fazer a transmissão. A thread principal irá gerar leituras aleatórias e armazenar 
em um buffer.
'''
class DispositivoIoT(threading.Thread):
    def __init__(self, dispositivo_id):
        threading.Thread.__init__(self)

        '''
        Configurações dos dispositivos
        '''
        self.id = dispositivo_id
        # Define qual o limite de velocidade que o dispositivo detecta
        self.limite = LIMITES[dispositivo_id%5]
        # buffer de leituras de velocidade
        self.leituras = deque(maxlen=50)


        logging.info(f"Dispositivo {dispositivo_id} iniciado")

        '''
        Configuração do publisher MQTT
        ''' 
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"iot_device_{dispositivo_id}",
            clean_session=False # False = que o client é persistente depois de desconectado
            )
        # Callbacks de eventos    
        self.client.enable_logger()
        self.client.on_connect = self._on_connect
        # self.client.on_connect_fail = self._on_connect_fail
        '''
        Configuração das threads que irão enviar dados ao broker
        '''
        self.lock = threading.Lock()
        self.send_thread = threading.Thread(target=self.thread_envio, daemon=True)
        self.stop = threading.Event()

        self.connect()

    '''
    Callback de conexão. Só irá ser acionada quando o publisher receber o ACK do broker
    '''
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            logging.error(f"Dispositivo {self.id} não conseguiu conectar ao broker")
        else:
            logging.info(f"Dispositivo {self.id} conectado ao Broker")

    '''
    Callback de conexão. Só irá ser acionada quando o pubisher receber uma resposta de rejeição do broker
    '''
    def _on_connect_fail(self,client, userdata):
        logging.error(f"Dispositivo {self.id} não conseguiu conectar ao broker")
   
    
    '''
    Inicia a conexão com o broker do Eclipse Mosquitto
    '''
    def connect(self):
        try:
            self.client.connect(
                host=MQTT_BROKER,
                port=MQTT_PORT
            )
            self.send_thread.start()

            # Inicia o loop de network do mqtt. Sem este comando não é possível fazer publicações nem receber mensagens do broker
            self.client.loop_start()

        except Exception as e:
            logging.error(f"Dispositivo {self.id}: erro ao conectar - {e}")

            
    '''
    Rotina da thread de enviar as leituras no buffer.
    '''
    def thread_envio(self):

        while not self.stop.is_set():

            if  len(self.leituras):

                # Lock para ler o buffer de leituras. Sem alterar o buffer
                with self.lock:
                    leitura = self.leituras[0]

                # tentativa de envio
                try:
                    payload = json.dumps({
                        "id_dispositivo":leitura.id_dispositivo,
                        "limite": leitura.limite,
                        "data": leitura.data,
                        "velocidade": leitura.velocidade,
                        "placa": leitura.placa
                    })

                    info = self.client.publish(
                        topic=MQTT_TOPIC,
                        payload=payload,
                        qos=1       # Pelo menos uma vez
                    )

                    info.wait_for_publish(timeout=60)
                    # Espera a mensagem ser publicada com timeout de 1 segundo. Se sucedido remove a leitura do buffer
                    if info.is_published(): 
                        logging.info(f"Dispositivo {self.id} publicou")

                        with self.lock:
                            self.leituras.popleft()
                    else:
                        raise Exception("Publish timeout")
            
                except Exception as e:
                    logging.error(f"Despositivo {self.id} falha ao envio: {str(e)}")
                    time.sleep(0.5)


    '''
    Rotina principal do DispositivoIoT.
    no loop dessa Thread ele irá receber leituras de velocidade e armazenar no buffer de leituras.
    '''
    def run(self):
        time.sleep(0.5)
        while not self.stop.is_set():

            leitura = LeituraFormato(
                id_dispositivo=self.id,
                limite = self.limite,
                data = datetime.now(timezone.utc).isoformat(),
                velocidade = random.randint(0,self.limite+20),
                placa = PLACAS[random.randint(0, len(PLACAS)-1)]
            )

            # Bloqueia o buffer para registrar uma nova leitura
            with self.lock:
                self.leituras.append(leitura)

            # sleep entre 1 a 3 segundos. Apenas para simular períodos diferentes de leitura
            time.sleep(random.randint(1,3))


    '''
    Encerra a conexão do dispositivo com o broker
    '''
    def shutdown(self):
        self.stop.set()
        self.send_thread.join()
        self.client.loop_stop()
        self.client.disconnect()


'''
Classe que irá inicializar os dispositivos
'''
class ClusterIoT():
    def __init__(self, n_dispositivos):
        self.dispositivos = [DispositivoIoT(n) for n in range(n_dispositivos)]
        self.running = False

    def run(self):

        if self.running:
            return

        self.running = True

        for dispositivo in self.dispositivos:
            dispositivo.start()

        for dispositivo in self.dispositivos:
            dispositivo.join()

    def stop(self):
        self.running = False
        for dispositivo in self.dispositivos:
            dispositivo.shutdown()

def main():
    os.makedirs("./logs", exist_ok=True)
    open("logs/logs.log","a+").close()
    startLog()
    n_threads = int(os.getenv("THREAD_COUNT"))
    try:
        cluster = ClusterIoT(n_threads)
        cluster.run()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cluster.stop()
        logging.info(f"Simulador encerrado")


if __name__ == "__main__":
    main()