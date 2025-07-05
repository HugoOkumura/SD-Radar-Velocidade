from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

'''
Nome: Hugo Naoki Sonoda Okumura
Criado: 27/06/2025
Última atualização: 29/06/2025
 # Este código implementa as funçonalidades para armazenar as leituras de velocidades, geradas pelos dispositivos
 # IoT, para o MongoDB Atlas. 
'''

URI = "mongodb+srv://admin:admin@sd.wrdeptn.mongodb.net/?retryWrites=true&w=majority&appName=SD"

'''
Classe que irá gerenciar as funções de requisição de banco
'''
class LeiturasManager:
    def __init__(self):
        self.mongo = MongoClient(URI, server_api=ServerApi('1'))
        self.db = self.mongo['SD_Projeto']
        self.collection = self.db['LeiturasVelocidade']

    '''
    Insere uma nova leitura no banco de dados
    '''
    def insert(self, data):
        leitura_documento = {
            "id_dispositivo" : data['id_dispositivo'],
            "limite": data['limite'],
            "data": data['data'],
            "velocidade": data['velocidade'],
            "placa": data['placa'],
            "infracao": True if data['velocidade'] > data['limite'] else False,
            "multa_registrada": False
        }

        print(leitura_documento)

        leitura_inserida = self.collection.insert_one(leitura_documento).acknowledged
        # se a inserção for aceita retorna 1 (sucesso)
        if leitura_inserida:
            return 1
        else:
            #retorna 0 (erro) caso contrário
            return 0

    '''
    Busca todas as leituras que são infrações de velocidade e ainda não geraram multas
    '''
    def retrieve_infracoes(self):
        infracoes = list(self.collection.find({
                        "infracao": True,
                        "multa_registrada": False
                    }))
        return infracoes
    
    '''
    Quando for gerado a multa muda o estado de {multa_registrada} para true no banco de dados
    '''
    def change_status(self, data):        
        leitura_editada = self.collection.find_one_and_update(
            {"_id":data['_id']},
            {"$set": {"multa_registrada": True}}
            )
        
        if leitura_editada:
            return 1
        return 0

# DEBUG CODE
# if __name__ == "__main__":
#     t = LeiturasManager()
#     try:
#         t.mongo.admin.command('ping')
#     except Exception as e:
#         print(e)

#     l = LeituraFormato(
#         id_dispositivo=2,
#         limite=60,
#         data=time.time(),
#         velocidade=80,
#         placa="TESTE"
#     )

#     # t.insert(l)

#     lista = t.retrieve_infracoes()
#     # print(lista[0].id)
#     # print(lista[0]['_id'])

#     t.change_status(lista[0])

    