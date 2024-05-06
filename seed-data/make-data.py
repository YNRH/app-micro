# this creates urlencode-friendly files without EOL
import urllib.parse

movies = ['Inception', 'The Matrix', 'The Godfather', 'Pulp Fiction', 'The Shawshank Redemption', 'Fight Club', 'Forrest Gump', 'The Dark Knight', 'Interstellar', 'Goodfellas']

for i, movie in enumerate(movies):
    outfile = open(f'post{i}', 'w')
    params = ({ 'vote': movie })
    encoded = urllib.parse.urlencode(params)
    outfile.write(encoded)
    outfile.close()
