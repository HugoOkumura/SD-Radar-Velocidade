from flask import Flask, render_template, request, redirect, url_for, session
import requests
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
BACKEND_URL = os.getenv('API_MULTAS')  # Nome do serviço no docker-compose

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/multas",
            auth=(session['username'], session['password'])
        )
        
        if response.status_code == 200:
            multas = response.json()
            return render_template('index.html', multas=multas)
        else:
            return render_template('index.html', error="Erro ao carregar multas")
    except requests.exceptions.RequestException:
        return render_template('index.html', error="Não foi possível conectar ao servidor")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            response = requests.get(
                f"{BACKEND_URL}/validate_login",
                auth=(username, password)
            )
            
            if response.status_code == 200:
                session['username'] = username
                session['password'] = password
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error="Credenciais inválidas")
        except requests.exceptions.RequestException:
            return render_template('login.html', error="Serviço indisponível")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('password', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)