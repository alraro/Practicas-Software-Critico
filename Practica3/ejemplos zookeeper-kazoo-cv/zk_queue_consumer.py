from kazoo.client import KazooClient
from kazoo.recipe.queue import Queue
import time

# Conectar con ZooKeeper
client = KazooClient(hosts="localhost:2181")
client.start()

# Crear la cola en la misma ruta
queue = Queue(client, "/queue/demo")

print("Consumidor activo. Leyendo valores sin bloquear...\n")

for _ in range(20):  # Intentos de lectura
    item = queue.get()  # NO bloquea, solo 1 consumidor obtiene cada elemento
    if item:
        print(f"[CONSUMIDOR] Consumido: {item.decode('utf-8')}")
    else:
        print("[CONSUMIDOR] Cola vacía, esperando...")
    time.sleep(1)

print("Fin del consumidor.")
client.stop()