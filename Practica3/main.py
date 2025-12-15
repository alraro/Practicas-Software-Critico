from kazoo.client import KazooClient
from kazoo.recipe.election import Election
import os
import sys
import random
from time import sleep
import threading
import requests

ZOOKEEPER_HOSTS = os.getenv("ZOOKEEPER_HOSTS", "").strip()
MEDICIONES_PATH = "mediciones"
ELECTION_PATH = "election_path"
URL="http://host.docker.internal:4000/detectar"

def send_metric(URL, value):
    try:
        response = requests.get(URL + "?dato=" + str(value))
        print(f"Sent value {value} to {URL}, response status: {response.status_code}")
    except Exception as e:
        print(f"Error sending value {value} to {URL}: {e}")

def get_values_from_children(zk, node_id):
    values = []
    children = zk.get_children(f"/{MEDICIONES_PATH}")
    print(f"Leader Node {node_id} - Current Measurements:")
    for child in children:
        data, _ = zk.get(f"/{MEDICIONES_PATH}/{child}")
        try:
            value = float(data.decode('utf-8'))
            values.append(value)
            print(f"  Node {child}: {value} ")
        except ValueError:
            print(f"  Node {child}: Invalid data")
    return values

def trabajo_lider(zk, node_id):
    print(f"Node {node_id} is now the leader.")
    try:
        while True:
            if zk.exists(f"/{MEDICIONES_PATH}"):
                values = get_values_from_children(zk, node_id)
                if values:
                    media = sum(values) / len(values)
                    print(f"  Average Measurement: {media}")
                    send_metric(URL, media)
                else:
                    print("  No valid measurements to calculate average.")
            else:
                print(f"Leader Node {node_id} - No measurements found in /{MEDICIONES_PATH}.")
            sleep(5)
    except Exception as e:
        print(f"Leader Node {node_id} encountered an error: {e}")
                    
def publicar_medicion_ephemeral(zk, node_id):
    while True:
        try:
            measure = random.normalvariate(70, 5)
            print(f"Node {node_id} - Measure: {measure}")
            if zk.exists(f"/{MEDICIONES_PATH}/{node_id}"):
                zk.set(f"/{MEDICIONES_PATH}/{node_id}", str(measure).encode("utf-8"))
            else:
                zk.create(f"/{MEDICIONES_PATH}/{node_id}", str(measure).encode("utf-8"), ephemeral=True)
        except Exception as e:
            print(f"Error in node {node_id}: {e}")
        finally:
            sleep(5)

def main():
    if not ZOOKEEPER_HOSTS:
        print("No Zookeeper hosts provided.")
        return
    else:
        zk = KazooClient(hosts=ZOOKEEPER_HOSTS)
        zk.start()
        print(f"Connected to Zookeeper at {ZOOKEEPER_HOSTS}")

    argc = len(sys.argv)
    if argc != 2:
        print("Usage: python main.py <node_id>")
        return
    
    node_id = int(sys.argv[1])
    print(f"Running node with ID: {node_id}")
    
    medidor = threading.Thread(target=publicar_medicion_ephemeral, args=(zk, node_id), daemon=True)
    medidor.start()
    
    elector = Election(zk, f"/{ELECTION_PATH}", identifier=str(node_id))
    elector.run(lambda: trabajo_lider(zk, node_id))
    
if __name__ == "__main__":
    main()