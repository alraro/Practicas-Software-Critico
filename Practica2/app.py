from flask import Flask, request
from redis import Redis, RedisError
from datetime import datetime
import os
import socket


# Connect to Redis
REDIS_HOST = os.getenv('REDIS_HOST', "localhost")
print("REDIS_HOST: "+REDIS_HOST)
redis = Redis(host=REDIS_HOST, db=0, socket_connect_timeout=2, socket_timeout=2)

app = Flask(__name__)

@app.route("/")
def hello():
    try:
        visits = redis.incr("counter")
    except RedisError:
        visits = "<i>cannot connect to Redis, counter disabled</i>"

    html = "<h3>Hello {name}!</h3>" \
           "<b>Hostname:</b> {hostname}<br/>" \
           "<b>Visits:</b> {visits}"
    return html.format(name=os.getenv("NAME", "world"), hostname=socket.gethostname(), visits=visits)


@app.route("/nuevo")
def nuevo():
    dato = request.args.get('dato')
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        if (dato == "") or (dato is None):
            respuesta = "Dato no proporcionado, no se agregó nada."
        else:
            redis.hset("mediciones", fecha, dato)
            respuesta = "Dato '"+dato+"' agregado a la lista."
    except RedisError:
        respuesta = "No se pudo conectar a Redis, dato no agregado."
    finally:
        return f"<p>{respuesta}</p>"

@app.route("/listar")
def listar():
    try:
        valores = redis.hgetall("mediciones")
        if not valores:
            return "<p>No hay datos almacenados.</p>"
        html = "<h3>Lista de Mediciones:</h3><ul>"
        for fecha, dato in valores.items():
            html += f"<li>{fecha.decode('utf-8')}: {dato.decode('utf-8')}</li>"
        html += "</ul>"
        return html
    except RedisError:
        return "<p>No se pudo conectar a Redis para listar los datos.</p>"

if __name__ == "__main__":
    PORT = os.getenv('PORT', 80)
    print("PORT: "+str(PORT))
    app.run(host='0.0.0.0', port=PORT)
