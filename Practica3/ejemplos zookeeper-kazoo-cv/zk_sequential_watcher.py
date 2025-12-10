from kazoo.client import KazooClient
from kazoo.recipe.watchers import ChildrenWatch
import time

# Conectar con ZooKeeper
client = KazooClient(hosts="localhost:2181")
client.start()

# Asegurar la ruta para nodos secuenciales
client.ensure_path("/sequence")

# Función watcher
def watch_sequence(children):
    if children:
        # Ordenar para encontrar el último nodo
        ultimo = sorted(children)[-1]
        print(f"[WATCHER] Nodos actuales: {children}")
        print(f"[WATCHER] Último nodo secuencial: {ultimo}")
    else:
        print("[WATCHER] No hay nodos secuenciales.")
    return True  # Mantener el watcher activo

# Registrar el watcher
ChildrenWatch(client, "/sequence", watch_sequence)

print("Watcher activo. Creando nodos secuenciales cada 2 segundos...\n")

# Simulación: crear nodos secuenciales
for i in range(5):
    path = client.create("/sequence/trigger-", b"", sequence=True)
    print(f"[SIMULACIÓN] Nodo creado: {path}")
    time.sleep(2)

print("Fin de la simulación.")
client.stop()