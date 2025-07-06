from flask import Flask, render_template, request, redirect, url_for, session
import requests

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'

THINGSBOARD_URL = 'http://iot.ceisufro.cl:8080/'  # Cambia esto a la IP o dominio de tu ThingsBoard

@app.route('/', methods=['GET', 'POST'])
def login():
    mensaje = ''
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']

        # Login contra ThingsBoard API
        response = requests.post(
            f'{THINGSBOARD_URL}/api/auth/login',
            json={'username': usuario, 'password': clave}
        )

        if response.status_code == 200:
            datos = response.json()
            session['usuario'] = usuario
            session['token'] = datos['token']
            return redirect(url_for('dashboard'))
        else:
            mensaje = 'Credenciales inválidas (ThingsBoard).'

    return render_template('login.html', mensaje=mensaje)

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session or 'token' not in session:
        return redirect(url_for('login'))

    # Verificar que el token JWT siga siendo válido
    headers = {'Authorization': f"Bearer {session['token']}"}
    response = requests.get(f'{THINGSBOARD_URL}/api/auth/user', headers=headers)

    if response.status_code != 200:
        session.clear()
        return redirect(url_for('login'))

    return render_template('dashboard.html', usuario=session['usuario'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)