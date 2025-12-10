from kazoo.client import KazooClient
from kazoo.recipe.queue import LockingQueue
import time

zk = KazooClient(hosts="127.0.0.1:2181")
zk.start()

queue = LockingQueue(zk, "/demo_queue")

for i in range(5):
    item = f"mensaje-{i}"
    queue.put(item.encode("utf-8"))
    print("Encolado:", item)
    time.sleep(5)

zk.stop()
