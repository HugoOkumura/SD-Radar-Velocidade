# SD-Radar-Velocidade
<p>Projeto de sistemas distribuídos. Implementando um sistema distribuído IoT.</p>

<p>O projeto implementa um sistema de radar de velocidade. Onde dispositivos IoT enviam leituras de velocidade e placa do carro para um serviço que irá analizar se houve uma infração. A comunicação entre este serviço e os dipositivos será feita utilizando o protocolo MQTT utilizando <a href="https://www.mosquitto.org/">Eclipse Mosquitto</a>.</p>

<p>Tendo uma infração ele irá armazenar os dados da infração para um banco de dados MongoDB, enviar estes dados para um serviço de notificação e um serviço de multas usando gRPC.</p>

<p>O serviço de notificação irá enviar a notificação de infração para um aplicativo web do usuário utilizando um protocolo de fila de mensagem usando <a href="https://www.rabbitmq.com/"> RabbitMQ </a>.</p>

<p>O serviço de multas será uma API que, ao receber as infrações, irá analizar a placa do veículo procurar no banco de dados um usuário com o veículo com esta placa e criar uma multa relacionada a esse usuário.</p>

<p>Com isso, o usuário terá um aplicativo web que irá receber as notificações do serviço de notificação usando o RabbitMQ. E irá poder acessar o serviço de multas usando um protocolo REST para acessar todas suas multas registradas.</p>


## Arquitetura do Sistema

<image src="./Arquitetura_Projeto_SD.png">

## Interfaces de Serviço


