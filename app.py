from flask import Flask, render_template, request, jsonify, session
import mysql.connector
from rapidfuzz import process, fuzz
import re

app = Flask(__name__)
app.secret_key = "clave_super_segura"  # Necesaria para usar sesiones


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="farmacia"
    )


intenciones = {
    "saludos": ["hola", "wuenas", "holi", "holaa", "buenas", "qué tal", "que tal", "hi", "hello", "holla",
                "buenos dias", "buenas noches", "buenas tardes", "hole", "oe", "oye"],
    "despedidas": ["adios", "adiós", "chao", "nos vemos", "hasta luego", "bye", "hasta nunca", "gracias por todo", "gracias", "te agradezco"],
    "estado": ["como estas", "cómo estás", "que tal", "qué tal", "como vas", "que bueno", "bien", "muy bien"],
    "acciones": ["que haces", "qué haces", "que estas haciendo", "necesito ayuda", "ayudame", "me puedes ayudar", "me ayudas", "necesito tu ayuda"],
    "productos": ["productos tienes", "ver productos", "mostrar productos", "quiero ver los productos",
                  "deja ver los productos", "no tienes mas productos", "no tienes más productos",
                  "hay más productos", "quiero ver mas productos", "muestrame los productos"],
    "horario": ["horario", "hora", "a qué hora abren", "a qué hora cierran", "horarios disponibles",
                "que horarios tienes", "cual es el horario", "que horario hay"],
    "direccion": ["dónde están", "ubicación", "dirección", "direccion",
                  "cómo llegar", "como llegar", "cual es tu direccion", "cual es tu dirección", "cual es tu ubicacion",
                  "donde queda", "donde estan ubicados", "donde esta ubicada la farmacia"],
    "descuentos": ["descuento", "oferta", "promocion", "rebaja"],
    "sintomas": ["dolor de cabeza", "fiebre", "tos", "dolor de estomago", "gripe", "resfriado",
                 "dolor garganta", "mareo", "dolor muscular", "insomnio", "estres"],
    "presentacion": ["me llamo", "soy", "mi nombre es"]
}

respuestas_sintomas = {
    "dolor de cabeza": "Para dolor de cabeza, puedes considerar paracetamol o ibuprofeno. Recuerda seguir las indicaciones del envase.",
    "fiebre": "Para la fiebre, paracetamol o ibuprofeno pueden ayudar. Mantente hidratado y consulta a un médico si la fiebre persiste.",
    "tos": "Para la tos, jarabes expectorantes o miel pueden ser útiles.",
    "dolor de estomago": "Para dolor de estómago, evita comidas pesadas y considera antiácidos si es necesario.",
    "gripe": "Para la gripe, descanso, hidratación y analgésicos comunes pueden aliviar los síntomas.",
    "resfriado": "Para resfriado, líquidos calientes y descanso son recomendables.",
    "dolor garganta": "Gárgaras con agua salada y pastillas para la garganta pueden ayudar.",
    "mareo": "Para mareo, descansa y evita movimientos bruscos. Hidratación es clave.",
    "dolor muscular": "Para dolor muscular, puedes usar analgésicos tópicos o tomar un baño caliente.",
    "insomnio": "Para insomnio, intenta relajarte antes de dormir y evitar pantallas.",
    "estres": "Para estrés, técnicas de respiración, caminatas y descanso pueden ayudar."
}


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    mensaje = data.get("mensaje", "").lower().strip()
    nombre_usuario = session.get("nombre", None)

    respuesta = "Lo siento, no entendí tu solicitud. Puedes preguntarme sobre productos, horarios, dirección, descuentos o síntomas. 😊"

    # 🟢 SALUDOS
    if any(p in mensaje for p in intenciones["saludos"]):
        if nombre_usuario:
            respuesta = f"¡Hola {nombre_usuario}! 😊 ¿Quieres ver los productos, el horario o la dirección?"
        else:
            respuesta = "¡Hola! 😊 ¿Quieres ver los productos, el horario o la dirección?, estoy a tu disposición"

    # 🟢 DESPEDIDAS (ahora olvida el nombre)
    elif any(p in mensaje for p in intenciones["despedidas"]):
        respuesta = f"¡Hasta luego {nombre_usuario if nombre_usuario else ''}! 😊 Si necesitas ayuda nuevamente, estaré aquí."
        session.pop("nombre", None)  # 🔹 borra el nombre guardado

    # 🟢 ESTADO
    elif any(p in mensaje for p in intenciones["estado"]):
        respuesta = "¡Estoy muy bien! Gracias por preguntar 😊, espero que también estés muy bien."

    # 🟢 AYUDA
    elif any(p in mensaje for p in intenciones["acciones"]):
        respuesta = "Estoy aquí para ayudarte 💻. Pregúntame por productos, horarios, dirección, descuentos o síntomas."

    # 🟢 HORARIO
    elif any(p in mensaje for p in intenciones["horario"]):
        respuesta = "Nuestro horario es de lunes a sábado de 8:00 AM a 8:00 PM 🕗"

    # 🟢 DIRECCIÓN
    elif any(p in mensaje for p in intenciones["direccion"]):
        respuesta = "La farmacia está ubicada en Fusagasugá, Cundinamarca, Colombia 🇨🇴."

    # 🟢 DESCUENTOS
    elif any(p in mensaje for p in intenciones["descuentos"]):
        respuesta = "Tenemos descuentos de hasta un 20% en algunos medicamentos 💰."

    # 🟢 PRESENTACIÓN
    elif any(p in mensaje for p in intenciones["presentacion"]):
        nombre_match = re.search(r"(?:soy|me llamo|mi nombre es)\s+([a-záéíóúñ]+)", mensaje)
        if nombre_match:
            nombre = nombre_match.group(1).capitalize()
            session["nombre"] = nombre
            respuesta = f"¡Encantado de conocerte, {nombre}! 😊 ¿En qué puedo ayudarte hoy?"
        else:
            respuesta = "¡Encantado de conocerte! 😊 ¿En qué puedo ayudarte hoy?"

    else:
        # 🔹 Conexión a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nombre, precio, IFNULL(stock, 20) AS stock FROM productos")
        productos = cursor.fetchall()
        cursor.close()
        conn.close()

        # 🟢 MOSTRAR PRODUCTOS
        if any(p in mensaje for p in intenciones["productos"]):
            tabla = "<div class='tabla-container'><table class='tabla-productos'><thead><tr><th>Nombre</th><th>Precio</th></tr></thead><tbody>"
            for p in productos:
                tabla += f"<tr><td>{p['nombre']}</td><td>${p['precio']}</td></tr>"
            tabla += "</tbody></table></div>"
            respuesta = tabla

        else:
            # 🟢 PRIMERO: detectar síntomas
            mejor_sintoma = process.extractOne(mensaje, list(respuestas_sintomas.keys()), score_cutoff=70)
            if mejor_sintoma:
                sintoma = mejor_sintoma[0]
                respuesta = respuestas_sintomas[sintoma]

            else:
                # 🟢 SEGUNDO: buscar productos
                nombres_productos = [p["nombre"].lower() for p in productos]
                mejor_producto = process.extractOne(mensaje, nombres_productos, score_cutoff=60)
                if mejor_producto:
                    nombre_encontrado = mejor_producto[0]
                    producto_info = next(p for p in productos if p["nombre"].lower() == nombre_encontrado)

                    cantidad_match = re.search(r"(?:quiero|dame|necesito|comprar)\s+(\d+)", mensaje)
                    if cantidad_match:
                        cantidad = int(cantidad_match.group(1))
                        if cantidad <= producto_info['stock']:
                            respuesta = f"{nombre_usuario+', ' if nombre_usuario else ''}Perfecto 😊, te he reservado {cantidad} unidades de {producto_info['nombre']}. Aún quedan {producto_info['stock'] - cantidad} disponibles."
                        else:
                            respuesta = f"Lo siento 😔, solo tenemos {producto_info['stock']} unidades de {producto_info['nombre']} disponibles."
                    
                    elif any(palabra in mensaje for palabra in ["cuantos", "cantidad", "tienes", "quedan", "disponibles"]):
                        respuesta = f"{nombre_usuario+', ' if nombre_usuario else ''}Actualmente tenemos {producto_info['stock']} unidades de {producto_info['nombre']} disponibles."

                    elif any(palabra in mensaje for palabra in ["precio", "cuesta", "vale", "a como", "a cuánto", "cuánto", "cuanto"]):
                        respuesta = f"{nombre_usuario+', ' if nombre_usuario else ''}Cada unidad de {producto_info['nombre']} cuesta ${producto_info['precio']}."

                    else:
                        respuesta = f"{nombre_usuario+', ' if nombre_usuario else ''}Sí, tenemos {producto_info['nombre']} a ${producto_info['precio']}."

    return jsonify({"respuesta": respuesta})


if __name__ == "__main__":
    app.run(debug=True)
