from flask import Flask, request
from redis import Redis, RedisError, Sentinel
from redis.cluster import RedisCluster, ClusterNode
from datetime import datetime
import time
import os
import socket
import tensorflow as tf
import numpy as np
from joblib import load
import sklearn as skl

def get_redis_standalone_client():
	REDIS_HOST = os.getenv('REDIS_HOST', "localhost")
	print("Connecting to Redis in standalone mode at host: "+REDIS_HOST)
	return Redis(host=REDIS_HOST, db=0, socket_connect_timeout=2, socket_timeout=2)

def get_redis_sentinel_client():
	print("Connecting to Redis in Sentinel mode")
	sentinel_hosts = os.getenv('REDIS_SENTINEL_HOSTS', "localhost:26379").split(',')
	sentinel = Sentinel([(host.split(':')[0], int(host.split(':')[1])) for host in sentinel_hosts], socket_timeout=0.1)
	print("Sentinel hosts: ", sentinel_hosts)
	print("Master info: ", sentinel.discover_master('mymaster'))
	return sentinel.master_for('mymaster', socket_timeout=2)

def get_redis_cluster_client():
	startup_nodes_str = os.getenv('REDIS_CLUSTER_NODES', "localhost:6379")
	startup_nodes = []
	for node in startup_nodes_str.split(','):
		host, port = node.split(':')
		startup_nodes.append(ClusterNode(host=host, port=int(port)))
		print(f"Cluster node created: Host={host}, Port={port}")
	
	print("Connecting to Redis in Cluster mode with nodes: ", startup_nodes)
	redis = RedisCluster(
		startup_nodes=startup_nodes,
		decode_responses=False,
		socket_connect_timeout=2,
		socket_timeout=2,
		skip_full_coverage_check=True
	)
	return redis

def get_redis_client(mode):
	if (mode == 'standalone'):
		return get_redis_standalone_client()
	elif (mode == 'sentinel'):
		return get_redis_sentinel_client()
	elif (mode == 'cluster'):
		return get_redis_cluster_client()
	else:
		print(f"Unknown REDIS_MODE: {mode}")
		exit(1)

redis_mode = os.getenv('REDIS_MODE', "standalone")
redis = get_redis_client(redis_mode)

model = tf.keras.models.load_model('lstm_autoencoder_model.keras')

model.summary()

scaler = load('scaler.pkl')

app = Flask(__name__)

def insert_ts_data(data, key='temperature', timestamp='*'):
	try:
		redis.execute_command('TS.ADD', key, timestamp, data)
	except RedisError as e:
		print(f"Error inserting data into RedisTimeSeries: {e}")

def get_ts_data(key='temperature', count=-1):
	try:
		if count != -1:
			return redis.execute_command('TS.REVRANGE', key, '-', '+', 'COUNT', count)
		else:
			return redis.execute_command('TS.RANGE', key, '-', '+')
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
	res = {}
	data_list = []
	try:
		valores = get_ts_data()
		for dato in valores:
			data_list.append({"timestamp": dato[0], "value": float(dato[1].decode('utf-8'))})
   
		res['hostname'] = socket.gethostname()
		res['data'] = data_list
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
	# Usar el mismo umbral que guardaste en umbral_mae.txt
	threshold = 0.0388 
	window_size = 12
	
	try:
		if (data == "") or (data is None):
			res.append({"error": "Empty input error"})
			return res # Retornar inmediatamente

		# Obtenemos los 11 datos anteriores para completar la ventana con el actual
		# get_ts_data con REVRANGE nos dará: [Dato(t-1), Dato(t-2), ..., Dato(t-11)]
		past_window = get_ts_data(count=window_size - 1)
		
		# Validar que tenemos suficientes datos históricos
		if len(past_window) < (window_size - 1):
			 # Si no hay suficientes datos, solo guardamos el dato sin predecir
			data_val = float(data)
			insert_ts_data(data_val)
			res.append({"error": "Not enough data history to fill window", "data": data_val})
			return res

		# Preparamos el array de valores
		# Como get_ts_data(REVRANGE) devuelve [Nuevo -> Viejo],
		# reversed(past_window) lo convierte en [Viejo -> Nuevo] (Cronológico: t-11 ... t-1)
		past_values = [float(x[1].decode('utf-8')) for x in reversed(past_window)]
		data_val = float(data)
		
		# Creamos la ventana completa de 12 elementos: [t-11, ..., t-1, t_actual]
		full_window = np.array(past_values + [data_val])
		
		# Preprocesamiento (Escalado) igual que en el entrenamiento
		# Reshape a (-1, 1) porque el scaler espera columna
		window_scaled = scaler.transform(full_window.reshape(-1, 1))
		
		# Reshape para el modelo LSTM: (1 muestra, 12 pasos, 1 característica)
		X_input = window_scaled.reshape(1, window_size, 1)

		# Predicción (Reconstrucción)
		X_pred = model.predict(X_input, verbose=0) # verbose=0 para limpiar logs

		# Cálculo del Error (MAE)
		# El modelo devuelve la reconstrucción de la ventana.
		# Calculamos el error promedio de reconstrucción de esta ventana.
		mae_loss = np.mean(np.abs(X_pred - X_input))

		print(f"DEBUG: Real: {data_val}, MAE Loss: {mae_loss:.5f}, Threshold: {threshold}")

		# --- Lógica de recuperación del valor esperado ---
		# Obtenemos el valor que el modelo "reconstruyó" para el último paso (el actual)
		# X_pred tiene forma (1, 12, 1), el último es el índice -1
		val_reconstruido_scaled = X_pred[0, -1, 0]
		# Deshacemos el escalado para tener el valor real "sano"
		val_reconstruido = float(scaler.inverse_transform([[val_reconstruido_scaled]])[0][0])


		# Preparar respuesta con el formato solicitado
		# Formato de mediciones: "time" y "valor"
		mediciones_serializables = [
			{"time": int(dato[0]), "valor": float(dato[1].decode('utf-8'))} 
			for dato in reversed(past_window)
		]
		
		mediciones_serializables.append({"time": int(time.time()*1000), "valor": data_val})

		# Detección de Anomalía (si/no)
		es_anomalia = mae_loss > threshold
		
		res.append({
			"mediciones": mediciones_serializables, 
			"anomalia": "si" if es_anomalia else "no",
		})

		# Insertar en Redis (Lógica de Sanitación)
		if es_anomalia:
			# Si es anomalía, NO guardamos el dato real corrupto.
			# Guardamos el valor reconstruido (suavizado) para mantener la ventana limpia.
			print(f"ANOMALIA: Guardando valor sanitizado {val_reconstruido:.4f} en lugar de {data_val}")
			insert_ts_data(val_reconstruido)
		else:
			# Si es normal, guardamos el dato real.
			insert_ts_data(data_val)

	except RedisError as e:
		res.append({"Redis error": str(e)})
	except Exception as e:
		# Es bueno imprimir el stacktrace en consola para depurar
		import traceback
		traceback.print_exc()
		res.append({"error": str(e)})
	
	return res

if __name__ == "__main__":
	PORT = os.getenv('PORT', 5000)
	print("PORT: "+str(PORT))
	app.run(host='0.0.0.0', port=PORT)
