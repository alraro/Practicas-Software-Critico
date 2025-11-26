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

def insert_ts_data(data, key='temperature', timestamp='*'):
	try:
		redis.execute_command('TS.ADD', key, timestamp, data)
	except RedisError as e:
		print(f"Error inserting data into RedisTimeSeries: {e}")

def get_ts_data(key='temperature', from_time='-', to_time='+', count=-1):
	try:
		if count != -1:
			return redis.execute_command('TS.RANGE', key, from_time, to_time, 'COUNT', count)
		else:
			return redis.execute_command('TS.RANGE', key, from_time, to_time)
	except RedisError as e:
		print(f"Error retrieving data from RedisTimeSeries: {e}")
		return []

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
			insert_ts_data(float(data))
			res.append({"data": data, "message": f"New input {data} added."})
	except RedisError as e:
		res.append({"error": str(e)})
	finally:
		return res
@app.route("/listar")
def listar():
	res = []
	try:
		valores = get_ts_data()
		for dato in valores:
			res.append({"timestamp": dato[0], "value": float(dato[1].decode('utf-8'))})
	except RedisError as e:
		res.append({"error": str(e)})
	finally:
		return res

def is_float(value):
	try:
		float(value)
		return True
	except ValueError:
		return False

@app.route("/detectar")
def detectar():
	res = []
	data = request.args.get('dato')
	threshold = 0.0388
	window_size = 12
	if not is_float(data):
		res.append({"error": "Invalid input error"})
		return res
	try:
		if (data == "") or (data is None):
			res.append({"error": "Empty input error"})
		else:
			window = get_ts_data(count=window_size)
			window_values = np.array(list((map(lambda x: float(x[1].decode('utf-8')), reversed(window)))))
			data_val = float(data)
			if (len(window) < window_size):
				res.append({"error": "Not enough data for anomaly detection"})
			else:
				prediccion = model.predict(window_values.reshape(1, 12, 1))
				error = abs(data_val - float(prediccion[0][0].item()))
				mediciones_serializables = [{"timestamp": int(dato[0]), "value": float(dato[1].decode('utf-8'))} for dato in window]
				if error > threshold:
					res.append({"mediciones": mediciones_serializables, "anomalia": True})
				else:
					res.append({"mediciones": mediciones_serializables, "anomalia": False})
				res.append({"data": data_val, "message": f"New input {data_val} added."})
			insert_ts_data(data_val)
	except RedisError as e:
		res.append({"Redis error": str(e)})
	except Exception as e:
		res.append({"error": str(e)})
	finally:
		return res

if __name__ == "__main__":
	PORT = os.getenv('PORT', 80)
	print("PORT: "+str(PORT))
	app.run(host='0.0.0.0', port=PORT)
