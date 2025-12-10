from kazoo.client import KazooClient
from kazoo.recipe.watchers import ChildrenWatch
import time

# Conectar con ZooKeeper
client = KazooClient(hosts="localhost:2181")
client.start()

# Asegurar la ruta para dispositivos
client.ensure_path("/devices")


# Función watcher
def watch_devices(children):
    # Se van recibiendo TODOS los hijos que dependen de esa ruta
    print(f"[WATCHER] Dispositivos conectados: {children}")
    return True  # Mantener el watcher activo

# Registrar el watcher
ChildrenWatch(client, "/devices", watch_devices)

print("Watcher activo. Simulando conexión y desconexión de dispositivos...\n")

# Simulación: conectar y desconectar dispositivos
for i in range(3):
    device_name = f"device_{i}"
    client.create(f"/devices/{device_name}", b"online")
    print(f"[SIMULACIÓN] Conectado: {device_name}")
    time.sleep(2)

# Simulación: desconectar dispositivos
for i in range(3):
    device_name = f"device_{i}"
    client.delete(f"/devices/{device_name}")
    print(f"[SIMULACIÓN] Desconectado: {device_name}")
    time.sleep(2)

print("Fin de la simulación.")
client.stop()