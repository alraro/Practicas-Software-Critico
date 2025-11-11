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
    res = []
    data = request.args.get('dato')
    try:
        if (data == "") or (data is None):
            res.append({"error": "Empty input error"})
        else:
            redis.execute_command('TS.ADD', 'temperature', '*', data)
            res.append({"data": data, "message": f"New input {data} added."})
    except RedisError:
        res.append({"error": "Redis connection error"})
    finally:
        return res
@app.route("/listar")
def listar():
    res = []
    try:
        valores = redis.execute_command('TS.RANGE', 'temperature', '-', '+')
        for dato in valores:
            res.append({"timestamp": dato[0], "value": float(dato[1].decode('utf-8'))})
    except RedisError:
        res.append({"error": "Redis connection error"})
    finally:
        return res
    
@app.route("/detectar")
def detectar():
    res = []
    data = request.args.get('dato')
    try:
        if (data == "") or (data is None):
            res.append({"error": "Empty input error"})
        else:
            temp = float(data)
            
    except RedisError:
        res.append({"error": "Redis connection error"})
    finally:
        return res

if __name__ == "__main__":
    PORT = os.getenv('PORT', 80)
    print("PORT: "+str(PORT))
    app.run(host='0.0.0.0', port=PORT)
