import os
import base64
import random
import string
import requests
from flask import Flask, request, redirect, jsonify, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

client_id = '89251c51d2d14ee4bb2575ffe6addb49'  # Seu ID de cliente Spotify
client_secret = '98b0de3612d84aeea3384c0640add886'  # Seu segredo Spotify
redirect_uri = "http://localhost:8181" # Sua URI de redirecionamento Spotify

def generate_random_string(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

@app.route('/login')
def login():
    state = generate_random_string(16)
    session['state'] = state

    # Sua aplicação solicita autorização
    scope = 'user-read-private user-read-email'
    auth_url = 'https://accounts.spotify.com/authorize?' + \
               f'response_type=code&' \
               f'client_id={client_id}&' \
               f'scope={scope}&' \
               f'redirect_uri={redirect_uri}&' \
               f'state={state}'
    return redirect(auth_url)

@app.route('/callback')
def callback():
    # Sua aplicação solicita tokens de atualização e acesso
    # após verificar o parâmetro de estado

    code = request.args.get('code')
    state = request.args.get('state')
    stored_state = session.get('state')

    if state is None or state != stored_state:
        return jsonify({'error': 'state_mismatch'}), 400

    session.pop('state', None)
    auth_options = {
        'url': 'https://accounts.spotify.com/api/token',
        'data': {
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        },
        'headers': {
            'Authorization': 'Basic ' + base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
        }
    }

    response = requests.post(**auth_options)
    data = response.json()

    if response.status_code == 200:
        access_token = data['access_token']
        refresh_token = data['refresh_token']

        options = {
            'url': 'https://api.spotify.com/v1/me',
            'headers': {'Authorization': 'Bearer ' + access_token}
        }

        # Use o token de acesso para acessar a API Web do Spotify
        response = requests.get(**options)
        user_data = response.json()
        print(user_data)

        # Também podemos passar o token para o navegador para fazer solicitações a partir daí
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token
        })

    return jsonify({'error': 'invalid_token'}), 400

@app.route('/refresh_token')
def refresh_token():
    # Solicitação de token de acesso a partir do token de atualização
    refresh_token = request.args.get('refresh_token')
    auth_options = {
        'url': 'https://accounts.spotify.com/api/token',
        'headers': {
            'Authorization': 'Basic ' + base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
        },
        'data': {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
    }

    response = requests.post(**auth_options)
    data = response.json()

    if response.status_code == 200:
        access_token = data['access_token']
        return jsonify({'access_token': access_token})

if __name__ == '__main__':
    app.run(port=8888)
