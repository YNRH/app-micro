# vote/app.py
from flask import Flask, render_template, request, make_response, g
from redis import Redis
import os
import socket
import random
import json
import logging

movies = ["Pulp Fiction", "The Shawshank Redemption", "Inception", "The Godfather", "Forrest Gump", 
          "The Matrix", "The Dark Knight", "Fight Club", "Interstellar", "The Lord of the Rings"]

def add_user_votes(voter_id, votes):
    redis = get_redis()
    for vote in votes:
        data = json.dumps({'voter_id': voter_id, 'vote': vote})
        redis.rpush('votes', data)

app = Flask(__name__)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="redis", db=0, socket_timeout=5)
    return g.redis

@app.route("/", methods=['POST','GET'])
def hello():
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]

    vote = None

    if request.method == 'POST':
        vote = [request.form.get(movie) for movie in movies]
        app.logger.info('Received votes for %s', vote)
        add_user_votes(voter_id, vote)

    resp = make_response(render_template(
        'index.html',
        movies=movies,
        hostname=socket.gethostname(),
        vote=vote,
    ))
    resp.set_cookie('voter_id', voter_id)
    return resp

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)