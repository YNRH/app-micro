# Seed-data/make-data.py
import random
import urllib.parse

movies = ['Inception', 'The Matrix', 'The Godfather', 'Pulp Fiction', 'The Shawshank Redemption', 'Fight Club', 'Forrest Gump', 'The Dark Knight', 'Interstellar', 'Goodfellas']

for i, movie in enumerate(movies):
    outfile = open(f'post{i}', 'w')
    params = { 'movie': movie, 'rating': random.randint(1, 5)} # Se incluye un rating aleatorio
    encoded = urllib.parse.urlencode(params)
    outfile.write(encoded)
    outfile.close()
