from kazoo.client import KazooClient
from kazoo.recipe.election import Election
import threading
import time
import random
import signal

# Definir una función que se ejecuta cuando se recibe la señal de interrupción
def interrupt_handler(signal, frame):
    exit(0)

# Registrar la función como el manejador de la señal de interrupción
signal.signal(signal.SIGINT, interrupt_handler)

# Crear un identificador para la aplicación
id = input("Introduce un identificador: ")

# Crear un cliente kazoo y conectarlo con el servidor zookeeper
client = KazooClient(hosts="127.0.0.1:2181")
client.start()

# Crear una elección entre las aplicaciones y elegir un líder
election = Election(client, "/election",id)

# Definir una función que se ejecuta cuando una aplicación es elegida líder
def leader_func():
    while True:
        print('soy lider')
        # Obtener los hijos de /mediciones
        # Calcular la media de los valores
        # Mostrar la media por consola
        # Enviar la media usando requests
        time.sleep(5)


# Definir una función que se encarga de lanzar la parte de la elección
def election_func():
    # Participar en la elección con el identificador de la aplicación
    election.run(leader_func)

# Crear un hilo para ejecutar la función election_func
election_thread = threading.Thread(target=election_func, daemon=True)
# Iniciar el hilo
election_thread.start()

# Enviar periódicamente un valor a una subruta de /mediciones con el identificador de la aplicación
while True:
    # Generar una nueva medición aleatoria
    value = random.randint(75, 85)

    # Actualizar el valor de /values asociado al nodo
 
    # Esperar 5 segundos
 