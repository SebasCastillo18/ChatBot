import mysql.connector
import random

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="farmacia"
)
cur = conn.cursor()

medicamentos = ["Acetaminofén", "Ibuprofeno", "Loratadina", "Amoxicilina", "Vitamina C", "Omeprazol", "Metformina", "Simvastatina", "Salbutamol", "Prednisona"]
concentraciones = ["100mg", "200mg", "250mg", "500mg", "10mg", "20mg", "50mg", "1000mg"]

productos = []
for i in range(10000):
    nombre = f"{random.choice(medicamentos)} {random.choice(concentraciones)}"
    descripcion = f"Descripción del producto {nombre}"
    precio = round(random.uniform(5000, 20000), 2)
    stock = random.randint(10, 500)
    productos.append((nombre, descripcion, precio, stock))

cur.executemany(
    "INSERT INTO productos (nombre, descripcion, precio, stock) VALUES (%s, %s, %s, %s)",
    productos
)

conn.commit()
cur.close()
conn.close()

print("✅ 10,000 productos insertados correctamente")
