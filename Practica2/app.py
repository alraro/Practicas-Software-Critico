from flask import Flask, request
from redis import Redis, RedisError
from datetime import datetime
import os
import socket
import tensorflow as tf
import numpy as np


# Connect to Redis
REDIS_HOST = os.getenv('REDIS_HOST', "localhost")
print("REDIS_HOST: "+REDIS_HOST)
redis = Redis(host=REDIS_HOST, db=0, socket_connect_timeout=2, socket_timeout=2)

model = tf.keras.models.load_model('lstm_autoencoder_model.keras')

model.summary()

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
	except RedisError as e:
		res.append({"error": str(e)})
	finally:
		return res
@app.route("/listar")
def listar():
	res = []
	try:
		valores = redis.execute_command('TS.RANGE', 'temperature', '-', '+')
		for dato in valores:
			res.append({"timestamp": dato[0], "value": float(dato[1].decode('utf-8'))})
	except RedisError as e:
		res.append({"error": str(e)})
	finally:
		return res
	
@app.route("/detectar")
def detectar():
	res = []
	data = request.args.get('dato')
	threshold = 0.0388
	window_size = 12
	try:
		if (data == "") or (data is None):
			res.append({"error": "Empty input error"})
		else:
			# Obtener las últimas `window_size` mediciones (REVRANGE con COUNT)
			window = redis.execute_command('TS.REVRANGE', 'temperature', '-', '+', 'COUNT', window_size)
			print("Raw Window:", window)
			window_values = np.array(list((map(lambda x: float(x[1].decode('utf-8')), reversed(window)))))
			print("Window Values:", window_values)
			print("Window:", window, "| Len ", len(window))
			if (len(window) < window_size):
				res.append({"error": "Not enough data for anomaly detection"})
				redis.execute_command('TS.ADD', 'temperature', '*', float(data))
				return res
			# Convertir entrada a float y preparar para la predicción
			data_val = float(data)
			prediccion = model.predict(window_values.reshape(1, window_size, 1))
			error = abs(data_val - float(prediccion[0][0]))
			if error > threshold:
				res.append({"mediciones": window, "anomalia": True})
			else:
				res.append({"mediciones": window, "anomalia": False})
			redis.execute_command('TS.ADD', 'temperature', '*', data_val)
			res.append({"data": data_val, "message": f"New input {data_val} added."})
	except RedisError as e:
		res.append({"Redis error": str(e)})
	except Exception as e:
		# Capturamos otros errores (shape del modelo, conversión, etc.) y los devolvemos
		res.append({"error": str(e)})
	finally:
		return res

if __name__ == "__main__":
	PORT = os.getenv('PORT', 80)
	print("PORT: "+str(PORT))
	app.run(host='0.0.0.0', port=PORT)
