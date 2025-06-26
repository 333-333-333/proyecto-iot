import sqlite3

# Conexión y creación de la base de datos
conn = sqlite3.connect('usuarios.db')
cursor = conn.cursor()

# Crear la tabla de usuarios
cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE NOT NULL,
    clave TEXT NOT NULL
)
''')

# Usuario por defecto (puedes cambiar los valores aquí)
usuario_default = 'admin'
clave_default = 'admin123'

# Insertar el usuario si no existe
try:
    cursor.execute('INSERT INTO usuarios (usuario, clave) VALUES (?, ?)', (usuario_default, clave_default))
    print(f'✅ Usuario por defecto creado: {usuario_default} / {clave_default}')
except sqlite3.IntegrityError:
    print('ℹ️ El usuario ya existe, no se creó uno nuevo.')

# Guardar y cerrar
conn.commit()
conn.close()

print('✔️ Base de datos y tabla listas.')