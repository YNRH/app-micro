# recommendation.py
from flask import Flask, jsonify, request
import psycopg2

app = Flask(__name__)

# Connect to your PostgreSQL database
conn = psycopg2.connect(user="postgres", password="postgres", host="db", database="DBmovies")

# Example endpoint to check if the server is running
@app.route('/')
def hello_world():
    return 'si funciona'

# Function to compute Manhattan distance between two users
def manhattan(rating1, rating2):
    distance = 0
    commonRatings = False
    for key in rating1:
        if key in rating2:
            distance += abs(rating1[key] - rating2[key])
            commonRatings = True
    return distance if commonRatings else -1  # Indicates no ratings in common

# Function to compute the nearest neighbor of a user
def computeNearestNeighbor(voter_id, cur):
    cur.execute("SELECT user_id FROM users WHERE voter_id = %s::varchar;", (voter_id,))
    user_id = cur.fetchone()[0]
    cur.execute("SELECT user_id, voter_id FROM users WHERE user_id != %s;", (user_id,))

    user_info = cur.fetchall()
    distances = []
    cur.execute("SELECT movie, rating FROM ratings WHERE user_id IN (SELECT user_id FROM users WHERE voter_id != %s);", (voter_id,))
    all_ratings = cur.fetchall()
    user_ratings = {movie: rating for movie, rating in all_ratings if rating}
    for user_id, voter_id_db in user_info:
        cur.execute("SELECT movie, rating FROM ratings WHERE user_id = %s;", (user_id,))
        row = cur.fetchall()
        rating = {movie: rating for movie, rating in row if rating}
        distance = manhattan(rating, user_ratings)
        distances.append((distance, voter_id_db))
    distances.sort()  # sort based on distance -- closest first
    return distances

# Function to recommend movies for a user
def recommend(voter_id, cur):
    nearest = computeNearestNeighbor(voter_id, cur)[0][1]
    recommendations = []
    cur.execute("SELECT movie, rating FROM ratings WHERE user_id = (SELECT user_id FROM users WHERE voter_id = %s);", (nearest,))
    neighbor_ratings = cur.fetchall()
    cur.execute("SELECT movie, rating FROM ratings WHERE user_id = (SELECT user_id FROM users WHERE voter_id = %s);", (voter_id,))
    user_ratings = cur.fetchall()
    user_ratings = {movie: rating for movie, rating in user_ratings if rating}
    for movie, rating in neighbor_ratings:
        if movie not in user_ratings:
            recommendations.append((movie, rating))
    return sorted(recommendations, key=lambda movieTuple: movieTuple[1], reverse=True)

# Endpoint to get recommendations for a specific user
@app.route('/recommendations/<string:voter_id>')
def get_recommendations(voter_id):
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE voter_id = %s;", (voter_id,))
    user_id = cur.fetchone()[0]
    recommendations = recommend(user_id, cur)
    cur.close()
    return jsonify(recommendations)

# Endpoint to get recommendations for all users
@app.route('/recommendations')
def get_all_recommendations():
    cur = conn.cursor()
    cur.execute("SELECT voter_id FROM users;")
    voters = cur.fetchall()
    recommendations = {}
    for voter_id, in voters:
        cur.execute("SELECT user_id FROM users WHERE voter_id = %s;", (voter_id,))
        user_id = cur.fetchone()[0]
        recommendations[voter_id] = recommend(user_id, cur)
    cur.close()
    return jsonify(recommendations)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
