import hashlib
import base64

def encrypt_password(password, salt="multas"):
    # Converte o salt para bytes
    salt_bytes = salt.encode('utf-8')
    
    # Converte a senha para bytes
    password_bytes = password.encode('utf-8')
    
    # Cria o hash PBKDF2-HMAC-SHA512
    hashed = hashlib.pbkdf2_hmac(
        'sha512',
        password_bytes,
        salt_bytes,
        100000  # Número de iterações
    )
    
    # Converte o hash para representação em base64
    hashed_b64 = base64.b64encode(hashed).decode('utf-8')
    
    # Converte o salt para base64 (para armazenamento)
    salt_b64 = base64.b64encode(salt_bytes).decode('utf-8')
    
    return {
        'password': password,
        'salt': salt_b64,
        'hashed_password': hashed_b64,
        'algorithm': 'PBKDF2-HMAC-SHA512',
        'iterations': 100000
    }

# Lista de senhas para criptografar
passwords = ["123mudar","AAAA",'BBBB','CCCC','DDDD','EEEE','FFFFF','GGGGG','HHHHH','IIII']

# Criptografa todas as senhas
encrypted_passwords = [encrypt_password(pwd) for pwd in passwords]

# Exibe os resultados
for result in encrypted_passwords:
    print(f"Senha original: {result['password']}")
    print(f"Senha criptografada (base64): {result['hashed_password']}")
    print("-" * 50)