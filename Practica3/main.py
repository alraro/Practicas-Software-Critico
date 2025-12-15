from kazoo.client import KazooClient
from kazoo.recipe.election import Election
from kazoo.recipe.barrier import Barrier
from kazoo.recipe.counter import Counter

import os
import sys
import random
from time import sleep
import threading
import requests

ZOOKEEPER_HOSTS = os.getenv("ZOOKEEPER_HOSTS", "").strip()
MEDICIONES_PATH = "mediciones"
ELECTION_PATH = "election"
BARRIER_PATH = "barrier"
COUNTER_PATH = "counter"
CONFIG_PATH = os.getenv("CONFIG_PATH", "config")
UPDATE_COUNTER = 0

SAMPLING_PERIOD = 5.0
URL=os.getenv("METRICS_URL", "http://host.docker.internal:4000/nuevo")

def send_metric(URL, value):
    try:
        response = requests.get(URL + "?dato=" + str(value))
        print(f"[INFO] Sent value {value} to {URL}, response status: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Error sending value {value} to {URL}: {e}")

def get_values_from_children(zk, node_id):
    values = []
    try:
        children = zk.get_children(f"/{MEDICIONES_PATH}")
        print(f"[LEADER NODE {node_id}] - Current Measurements:")
        for child in children:
            data, _ = zk.get(f"/{MEDICIONES_PATH}/{child}")
            try:
                value = float(data.decode('utf-8'))
                values.append(value)
                print(f"  Node {child}: {value} ")
            except ValueError:
                print(f"  Node {child}: Invalid data")
    except Exception as e:
        print(f"[ERROR] [LEADER NODE {node_id}] encountered an error while retrieving measurements: {e}")
        return []
    return values

def trabajo_lider(zk, node_id):
    print(f"[INFO] Node {node_id} is now the leader.")
    barrier = Barrier(zk, f"/{BARRIER_PATH}")
    counter = Counter(zk, f"/{COUNTER_PATH}")
    
    @zk.ChildrenWatch(f"/{MEDICIONES_PATH}")
    def watch_mediciones(children):
        print(f"[INFO] [LEADER NODE {node_id}] Measurements updated. Current nodes: {children}")
        
    while True:
        try:
            barrier.create()
            print(f"[INFO] [LEADER NODE {node_id}] Waiting at barrier for {SAMPLING_PERIOD} seconds.")
            sleep(SAMPLING_PERIOD)

            total_mediciones = counter.value
            if zk.exists(f"/{MEDICIONES_PATH}"):
                values = get_values_from_children(zk, node_id)
                if values:
                    media = sum(values) / len(values)
                    print(f"  Average Measurement: {media}")
                    send_metric(URL, media)
                else:
                    print(f"[ERROR] [LEADER NODE {node_id}] No valid measurements to calculate average.")
            else:
                print(f"[ERROR] [LEADER NODE {node_id}] No measurements found in /{MEDICIONES_PATH}.")
        except Exception as e:
            print(f"[ERROR] [LEADER NODE {node_id}] encountered an error: {e}")
        finally:
            print(f"[INFO] [LEADER NODE {node_id}] Releasing barrier.")
            barrier.remove()
            sleep(1)
                    
def publicar_medicion_ephemeral(zk, node_id):
    
    zk.ensure_path(f"/{BARRIER_PATH}")
    barrier = Barrier(zk, f"/{BARRIER_PATH}")
    zk.ensure_path(f"/{COUNTER_PATH}")
    counter = Counter(zk, f"/{COUNTER_PATH}")
    
    
    while True:
        try:
            measure = random.normalvariate(70, 5)
            print(f"[NODE {node_id}] - Measure: {measure}")
            if zk.exists(f"/{MEDICIONES_PATH}/{node_id}"):
                print(f"[NODE {node_id}] - Updating measurement.")
                zk.set(f"/{MEDICIONES_PATH}/{node_id}", str(measure).encode("utf-8"))
            else:
                print(f"[NODE {node_id}] - Creating ephemeral measurement node.")
                zk.create(f"/{MEDICIONES_PATH}/{node_id}", str(measure).encode("utf-8"), ephemeral=True, makepath=True)

            print(f"[NODE {node_id}] - Waiting at barrier.")
            barrier.wait()
            print(f"[NODE {node_id}] - Passed barrier.")

            counter += 1
            print(f"[NODE {node_id}] - Incremented counter to {counter.value}.")
            sleep(2)
        except Exception as e:
            print(f"[ERROR] [NODE {node_id}] encountered an error: {e}")

def setup_watchers(zk):
    zk.ensure_path(f"/{CONFIG_PATH}/sampling_period")
    zk.ensure_path(f"/{CONFIG_PATH}/api_url")
    
    @zk.DataWatch(f"/{CONFIG_PATH}/sampling_period")
    def watch_sampling_period(data, stat):
        global SAMPLING_PERIOD
        if data:
            try:
                SAMPLING_PERIOD = float(data.decode("utf-8"))
                print(f"[CONFIG] Updated SAMPLING_PERIOD to {SAMPLING_PERIOD}s")
            except ValueError:
                print(f"[ERROR] [CONFIG] Invalid SAMPLING_PERIOD value received: {data.decode('utf-8')}")
    
    @zk.DataWatch(f"/{CONFIG_PATH}/api_url")
    def watch_api_url(data, stat):
        global URL
        if data:
            URL = data.decode("utf-8")
            print(f"[CONFIG] Updated API URL to {URL}")

def main():
    try:
        global SAMPLING_PERIOD
        SAMPLING_PERIOD = float(os.getenv("SAMPLING_PERIOD", "5"))
    except ValueError:
        print(f"[ERROR] Invalid SAMPLING_PERIOD value, using default {SAMPLING_PERIOD}s")

    if not ZOOKEEPER_HOSTS:
        print("[ERROR] No Zookeeper hosts provided.")
        return
    else:
        zk = KazooClient(hosts=ZOOKEEPER_HOSTS)
        zk.start()
        print(f"[ERROR] Connected to Zookeeper at {ZOOKEEPER_HOSTS}")

    argc = len(sys.argv)
    if argc != 2:
        print("[ERROR] Usage: python main.py <node_id>")
        return
    
    
    setup_watchers(zk)
    node_id = int(sys.argv[1])
    print(f"[INFO] Running node with ID: {node_id}")
    
    medidor = threading.Thread(target=publicar_medicion_ephemeral, args=(zk, node_id), daemon=True)
    medidor.start()
    
    elector = Election(zk, f"/{ELECTION_PATH}", identifier=str(node_id))
    elector.run(lambda: trabajo_lider(zk, node_id))
    
if __name__ == "__main__":
    main()