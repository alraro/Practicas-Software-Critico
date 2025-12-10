from kazoo.client import KazooClient
from kazoo.recipe.barrier import Barrier

zk_hosts = "127.0.0.1:2181"
barrier_path = "/demo_barrier"

zk = KazooClient(hosts=zk_hosts)
zk.start()

while True:
  # Creamos la barrera
  barrier = Barrier(zk, barrier_path)
  barrier.create()

  print("Esperando en la barrera...")
  barrier.wait()  # Espera a que otro proceso libere la barrera
                  # Ojo! Si la barrera no existe, no espera
  print("La barrera ha sido liberada. Continuando...")

zk.stop()
