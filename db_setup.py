import mysql.connector

conn = mysql.connector.connect(host="localhost", user="root", password="")
cur = conn.cursor()

cur.execute("CREATE DATABASE IF NOT EXISTS farmacia CHARACTER SET utf8 COLLATE utf8_general_ci;")
cur.execute("USE farmacia;")

cur.execute("""
CREATE TABLE IF NOT EXISTS productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100),
    descripcion TEXT,
    precio DECIMAL(10,2),
    stock INT
)
""")

print("✅ Base de datos y tabla creada correctamente.")

conn.commit()
cur.close()
conn.close()
