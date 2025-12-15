from kazoo.client import KazooClient
import sys
import os

ZOOKEEPER_HOSTS = os.getenv("ZOOKEEPER_HOSTS", "").strip()
CONFIG_PATH = os.getenv("CONFIG_PATH", "config")

if len(sys.argv) != 3:
    print("Uso: python init_config.py <sampling_period> <api_url>")
    sys.exit(1)

sampling_period = sys.argv[1]
api_url = sys.argv[2]

try:
    client = KazooClient(hosts=ZOOKEEPER_HOSTS)
    client.start()

    # Crear/actualizar configuración
    client.ensure_path(f"/{CONFIG_PATH}")
    client.ensure_path(f"/{CONFIG_PATH}/sampling_period")
    client.set(f"/{CONFIG_PATH}/sampling_period", sampling_period.encode("utf-8"))
    client.ensure_path(f"/{CONFIG_PATH}/api_url")
    client.set(f"/{CONFIG_PATH}/api_url", api_url.encode("utf-8"))
    print(f"Configuración inicializada: periodo={sampling_period}s, url={api_url}")
    client.stop()
except Exception as e:
    print(f"Error al inicializar la configuración: {e}")
    sys.exit(1)