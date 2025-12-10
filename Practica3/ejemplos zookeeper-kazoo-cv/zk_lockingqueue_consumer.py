from kazoo.client import KazooClient
from kazoo.recipe.queue import LockingQueue
from kazoo.recipe.watchers import ChildrenWatch
import time

zk = KazooClient(hosts="127.0.0.1:2181")
zk.start()

queue = LockingQueue(zk, "/demo_queue")

print("Esperando elementos en la cola...")
while True:
        item = queue.get() # Obtiene elemento y adquiere lock
        if item:
            print("Recibido:", item.decode("utf-8"))
            queue.consume() # Elimina elemento y libera lock
        else:
            print("Cola vacía")
