import requests
url = 'https://jsonplaceholder.typicode.com/posts' # Definimos la URL a la que queremos hacer la petición
params = {'userId': 1} # Definimos el parámetro que queremos enviar
response = requests.get(url, params=params) # Hacemos la petición GET con el parámetro y guardamos la respuesta en una variable
if response.status_code == 200: # Comprobamos si la petición fue exitosa
    data = response.json() # Obtenemos los datos de la respuesta en formato JSON
    print(data) # Imprimimos los datos

