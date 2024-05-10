from flask import Flask, render_template, request, make_response, g
from redis import Redis
import os
import socket
import random
import json
import logging

# Lista de películas
movies = ["Pulp Fiction", "The Shawshank Redemption", "Inception", "The Godfather", "Forrest Gump", 
          "The Matrix", "The Dark Knight", "Fight Club", "Interstellar", "The Lord of the Rings"]

# Configuración de la aplicación Flask
app = Flask(__name__)

# Configuración del logger
gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

# Función para obtener una instancia de Redis
def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="redis", db=0, socket_timeout=5)
    return g.redis

# Función para agregar votos de usuario a Redis
def add_user_votes(voter_id, votes):
    redis = get_redis()
    for movie, rating in votes.items():
        data = json.dumps({'movie': movie, 'rating': rating})
        redis.hset(f'user_ratings:{voter_id}', movie, data)

# Ruta raíz de la aplicación
@app.route("/", methods=['POST','GET'])
def hello():
    # Obtener el ID del votante desde la cookie o generarlo si es necesario
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]

    vote = None

    # Manejar solicitudes POST
    if request.method == 'POST':
        # Obtener los votos de las películas del formulario y convertirlos a un diccionario
        vote = {movie: int(request.form.get(movie)) if request.form.get(movie) is not None else None for movie in movies}
        app.logger.info('Received votes for %s', vote)
        
        # Filtrar los votos para incluir solo aquellos que no son None
        filtered_vote = {movie: rating for movie, rating in vote.items() if rating is not None}
        
        # Agregar los votos del usuario a Redis
        add_user_votes(voter_id, filtered_vote)


    # Renderizar la plantilla HTML con los datos necesarios
    resp = make_response(render_template(
        'index.html',
        movies=movies,
        hostname=socket.gethostname(),
        vote=vote,
        voter_id=voter_id,
    ))

    # Configurar la cookie para rastrear el ID del votante
    resp.set_cookie('voter_id', voter_id)
    return resp

# Iniciar la aplicación Flask
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
