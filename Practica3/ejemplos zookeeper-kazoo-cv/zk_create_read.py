from kazoo.client import KazooClient
from kazoo.client import KazooState

zk = KazooClient(hosts='127.0.0.1:2181')
zk.start()

try:
    # Ensure a path, create if necessary
    zk.ensure_path("/my/favorite")

    # Create a node with data
    zk.create("/my/favorite/node", "a value".encode("utf-8"), ephemeral=True)
except:
    print('node creation exception (maybe exists)')

# Determine if a node exists
if zk.exists("/my/favorite"):
    # Do something
    print('exists')

# Print the data of a node (empty)
(data,_) = zk.get("/my/favorite")
print(data.decode("utf-8"))

# List the children
children = zk.get_children("/my/favorite")
print("There are %s children with names %s" % (len(children), children))

# Print the data of a node
(data,_) = zk.get("/my/favorite/node")
print(data.decode("utf-8"))

# Modify the data of a node
zk.set("/my/favorite/node", "a value modified".encode("utf-8"))

# Print the data of a node
(data,_) = zk.get("/my/favorite/node")
print(data.decode("utf-8"))

zk.stop()