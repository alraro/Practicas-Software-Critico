from kazoo.client import KazooClient
from kazoo.recipe.queue import Queue
import time
import random

# Conectar con ZooKeeper
client = KazooClient(hosts="localhost:2181")
client.start()

# Crear la cola en la ruta /queue/demo
queue = Queue(client, "/queue/demo")

print("Productor activo. Publicando valores cada 2 segundos...\n")

for i in range(10):
    valor = str(random.randint(1, 100))
    queue.put(valor.encode("utf-8"))
    print(f"[PRODUCTOR] Publicado: {valor}")
    time.sleep(2)

print("Fin del productor.")
client.stop()