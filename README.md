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

O usuário poderá acessar a todas as multas registradas acessando o aplicativo web localizado em localhost:8000, após o sistema ter inicializado.
No aplicativo, o usuário deverá oferecer um nome e senha para poder ver as multas de cada usuário.

## Configuração do ambiente

<ol>

<li> Acesse <a href="https://account.mongodb.com/account/login?signedOut=true">MongoDB Atlas</a> e entre em/crie uma conta. Após o login no Atlas, crie um cluster com o nome que preferir e um Database com o nome 'SD_Projeto' e crie 3 Collections com os nomes 'LeiturasVelocidade', 'Multas' e 'Usuarios'.

<li> Após isso em 'Overview' clique em Connect no Cluster criado e selecione a opção Drivers. Selecione as opções [Driver: Python - Version: 3.11 or later]. Após isso, copie a string de conexão localizada ao final da tela. Substitua o db_username e o db_password pelo seu username e password.

<li> No diretório raiz do projeto, crie um arquivo .env e escreva nele:

```
MONGO_URI="string-de-conexao-gerado-no-passo=anterior"
```

<li> Feito isso, abra um terminal no diretório raiz do projeto e execute:

```
docker compose build
```

<li> Ao finalizar o build do sistema, execute no terminal:

```
docker compose init_db
```
Isso irá criar na Collection Usuarios, alguns usuários para testar o projeto
</li>

<li> Ao finalizar o init_db, execute o comando:

```
docker compose up 
#ou
docker compose up -d # irá executar em segundo plano
```
Para inicializar o sistema
</li>

<li> Para observar as ações de cada componente do sistema, acesso o /logs/logs.log do componente desejado para ver o histórico das ações feitas por eles. 

<li> Para acessar o aplicativo web, acesse em um navegador o localhost:8000 para realizar os testes.

</ol>


## Lista de usuários criados na Collection Usuarios
<ul>
<li> nome:Hugo -  senha:123mudar 
<li> nome:AAAA -  senha:AAAA
<li> nome:BBBB - senha:BBBB
<li> nome:CCCC - senha:CCCC
<li> nome:DDDD - senha:DDDD
<li> nome:EEEE - senha:EEEE
<li> nome:FFFF - senha:FFFF
<li> nome:GGGG - senha:GGGG
<li> nome:HHHH - senha:HHHH
<li> nome:IIII - senha:IIII
</ul>