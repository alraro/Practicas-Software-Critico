from kazoo.client import KazooClient
from kazoo.recipe.barrier import Barrier

zk_hosts = "127.0.0.1:2181"
barrier_path = "/demo_barrier"

zk = KazooClient(hosts=zk_hosts)
zk.start()

while True:
    barrier = Barrier(zk, barrier_path)
    barrier.create() # Si la barrera ya existe no pasa nada

    input('Pulsar Enter para liberar barrera')
    print("Liberando la barrera...")
    barrier.remove()  # Libera a todos los procesos en espera

zk.stop()
