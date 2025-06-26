from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'

DATABASE = 'usuarios.db'

def obtener_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def verificar_usuario(usuario, clave):
    conn = obtener_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND clave = ?", (usuario, clave))
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None

def registrar_usuario(usuario, clave):
    try:
        conn = obtener_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (usuario, clave) VALUES (?, ?)", (usuario, clave))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  # Usuario ya existe

@app.route('/', methods=['GET', 'POST'])
def login():
    mensaje = ''
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']
        if request.form['accion'] == 'registrar':
            if registrar_usuario(usuario, clave):
                mensaje = 'Registrado correctamente. Ahora inicia sesión.'
            else:
                mensaje = 'El usuario ya existe.'
        elif request.form['accion'] == 'ingresar':
            if verificar_usuario(usuario, clave):
                session['usuario'] = usuario
                return redirect(url_for('dashboard'))
            else:
                mensaje = 'Usuario o contraseña incorrectos.'
    return render_template('login.html', mensaje=mensaje)

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', usuario=session['usuario'])

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)