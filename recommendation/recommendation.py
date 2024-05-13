# recommendation.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Connect to your PostgreSQL database
conn = psycopg2.connect(user="postgres", password="postgres", host="db", database="DBmovies")

# Function to compute Manhattan distance
def manhattan(rating1, rating2):
    distance = 0
    common_ratings = False 
    for key in rating1:
        if key in rating2:
            distance += abs(rating1[key] - rating2[key])
            common_ratings = True
    if common_ratings:
        return distance
    else:
        return -1  # Indicates no ratings in common

# Function to compute nearest neighbor
def compute_nearest_neighbor(user_id, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, movie_id, rating FROM ratings WHERE user_id != %s", (user_id,))
    rows = cursor.fetchall()
    
    users = {}
    cursor.execute("SELECT movie_id, rating FROM ratings WHERE user_id = %s", (user_id,))
    user_ratings = {row[0]: row[1] for row in cursor.fetchall()}
    
    for row in rows:
        if row[0] not in users:
            users[row[0]] = {}
        users[row[0]][row[1]] = row[2]
    
    distances = []
    for user, ratings in users.items():
        distance = manhattan(user_ratings, ratings)
        distances.append((distance, user))
    
    distances.sort()
    cursor.close()
    return distances

# Function to recommend movies
def recommend_movies(voter_id, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE voter_id = %s", (voter_id,))
    user_id = cursor.fetchone()[0]
    
    nearest = compute_nearest_neighbor(user_id, conn)[0][1]

    recommendations = []
    
    cursor.execute("SELECT movie_id, rating FROM ratings WHERE user_id = %s", (nearest,))
    neighbor_ratings = {row[0]: row[1] for row in cursor.fetchall()}
    
    cursor.execute("SELECT movie_id, rating FROM ratings WHERE user_id = %s", (user_id,))
    user_ratings = {row[0]: row[1] for row in cursor.fetchall()}
    
    for movie_id, rating in neighbor_ratings.items():
        if movie_id not in user_ratings:
            cursor.execute("SELECT movie FROM movies WHERE movie_id = %s", (movie_id,))
            movie_name = cursor.fetchone()[0]
            recommendations.append((movie_name, rating))
    
    cursor.close()
    return sorted(recommendations, key=lambda movieTuple: movieTuple[1], reverse=True)

# Endpoint to get recommendations for a specific user
@app.route('/recommendations/<string:voter_id>')
def get_recommendations(voter_id):
    try:
        recommendations = recommend_movies(voter_id, conn)
        return jsonify(recommendations), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint to get recommendations for all users
@app.route('/recommendations')
def get_all_recommendations():
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT voter_id FROM users")
        voters = [row[0] for row in cursor.fetchall()]
        all_recommendations = {}
        for voter_id in voters:
            all_recommendations[voter_id] = recommend_movies(voter_id, conn)
        cursor.close()
        return jsonify(all_recommendations), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
