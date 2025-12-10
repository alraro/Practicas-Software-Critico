from kazoo.client import KazooClient
from kazoo.recipe.watchers import DataWatch
import time

# Conectar con ZooKeeper
client = KazooClient(hosts="localhost:2181")
client.start()

# Asegurar que el nodo existe
client.ensure_path("/config/sampling_period")
client.set("/config/sampling_period", b"5")  # Valor inicial

# Función watcher
def watch_sampling_period(data, stat):
    if data:
        print(f"[WATCHER] Nuevo valor de sampling_period: {data.decode('utf-8')}")
    else:
        print("[WATCHER] Nodo eliminado")
    return True  # Mantener el watcher activo

# Registrar el watcher
DataWatch(client, "/config/sampling_period", watch_sampling_period)

print("Watcher activo. Simulando cambios cada 3 segundos...\n")

# Simular cambios en el nodo
for i in range(6):
    nuevo_valor = str(5 + i)
    client.set("/config/sampling_period", nuevo_valor.encode("utf-8"))
    print(f"[SIMULACIÓN] Valor cambiado a: {nuevo_valor}")
    time.sleep(3)

print("Fin de la simulación.")
client.stop()
