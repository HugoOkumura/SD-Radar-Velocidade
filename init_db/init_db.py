from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os

if __name__ == '__main__':

    usuarios = [
        {"_id":1,"nome":"Hugo","placa":"ABC1D23","senha":"FR7iKDdJUwpgAu6y/wqatVMy2y4da3Cv3G7KKUUHrMXbafJlepw/X5kLv5MUGxcjPA+9uP+rFRQSQHjSODrwoQ=="},
        {"_id":2,"nome":"AAAA","placa":"BRA2E19","senha":"GdSEn/sLdHWLE9BpxsdjGzTnl/po6M5YV4yKhgaFGu1ikpAOUDLRBJt2huBuQoxZGsWuRRyHKZEiPeld/HJzeg=="},
        {"_id":3,"nome":"BBBB","placa":"FGH5J67","senha":"eiVIzoGxXTuWpwy/HaB1xG9VE5z9qX0Q6GELgBflCKcqxqjnvQ6vprCC66NYMTucsJHlXGRb3lFYlOJVpCMcZQ=="},
        {"_id":4,"nome":"CCCC","placa":"KLM9N45","senha":"axfWHvlROJf45e5iK9+g7VzRVHu/B+VDbYfXZx0KQsTcgbF+Vk8hM+wkZMLKGHrGxX9YjBQt2mAeFdSOMoO3zA=="},
        {"_id":5,"nome":"DDDD","placa":"OPQ8R21","senha":"VkiyU5Z/mlNpgTI87Y6qjRfDvG/3mTfCAPD0O/imLWahjQyLgP2pSLM1ADdPdyDAJM/mm27UW3Tvvt7ihnM9dA=="},
        {"_id":6,"nome":"EEEE","placa":"STU3V90","senha":"II8We14I4q0YYtFjLoUWXD86orR5FWXvmdvuEe0BVeGJIg2o1v6SG6WNQ3vWpTqVXZXc9WMgMUUybvJ6REEWSQ=="},
        {"_id":7,"nome":"FFFF","placa":"WXY7Z34","senha":"Nfhsdq5IYWfvjGN2+LPPpnyaDz3KyuDbQR+z/jVK2iUIp+AZBlNQz7umeeNxdaPZi9lqeKWlLCuhgce7Cs5OqA=="},
        {"_id":8,"nome":"GGGG","placa":"JKL4M56","senha":"3/RBzbEgzUSDGIKloFn/fA0mKV403gGGR8EwMtirCJdA3z32/oXrK0K8n5RXnqUyC4VbxIWOt91cU7TvbIHu3Q=="},
        {"_id":9,"nome":"HHHH","placa":"DEF6G78","senha":"aVYf5Z23aDF8Q50XlFoe9k5xbUO6a7VMCt7/IqR3wNdwCLzCMPCwVbv51OhoR4mpMBH3iKwPGwuRVXAKm3OjxA=="},
        {"_id":10,"nome":"IIII","placa":"MNO1P29","senha":"zgdbA65l0FpkyCBa+wEG2k8PY5nbL3+/uNjfYx0F0be3azXFoONdDBSU26ICTmZRB8w+6caMG5SOgeeAjEwuOw=="}
    ]

    try:
        uri = os.getenv('MONGO_URI')
        mongo = MongoClient(uri ,server_api=ServerApi('1'))
        db = mongo['SD_Projeto']
        collection = db['Usuarios']

        for u in usuarios:
            collection.insert_one(u)

    except Exception as e:
        print(str(e))