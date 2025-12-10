from kazoo.client import KazooClient
from kazoo.recipe.counter import Counter

# Conectar a ZooKeeper
zk = KazooClient(hosts="127.0.0.1:2181")
zk.start()

# Crear un contador en la ruta /example_counter
counter = Counter(zk, "/example_counter")

# Inicializar el contador (opcional)
counter -= counter.value

# Incrementar el contador
counter += 1
print(f"Valor actual del contador: {counter.value}")

# Incrementar varias veces
for i in range(3):
    counter += 1
    print(f"Incremento {i+1}, valor: {counter.value}")

# Detener la conexión
zk.stop()