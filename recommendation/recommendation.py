# recommendation.py
from flask import Flask, jsonify, request
import psycopg2

app = Flask(__name__)

# Connect to your PostgreSQL database
conn = psycopg2.connect(user="postgres", password="postgres", host="db", database="DBmovies")

# Example endpoint to check if the server is running
@app.route('/')
def hello_world():
    return '¡La API está en funcionamiento!'

# Endpoint to get recommendations for a specific user
@app.route('/recommendations/<string:voter_id>')
def get_recommendations(voter_id):
    try:
        # Create a cursor object
        cur = conn.cursor()

        # Get user_id from voter_id
        cur.execute("SELECT user_id FROM users WHERE voter_id = %s", (voter_id,))
        user_id = cur.fetchone()

        if user_id is None:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        # Find recommendations for the user
        cur.execute("""
                    SELECT movie_id, movie, rating
                    FROM (
                        SELECT r.movie_id, m.movie, r.rating, 
                               ROW_NUMBER() OVER(PARTITION BY r.movie_id ORDER BY r.rating DESC) AS rn
                        FROM ratings r
                        JOIN movies m ON r.movie_id = m.movie_id
                        WHERE r.user_id <> %s
                        AND r.movie_id NOT IN (
                            SELECT movie_id FROM ratings WHERE user_id = %s
                        )
                    ) ranked
                    WHERE rn = 1
                    ORDER BY rating DESC
                    LIMIT 10;
                    """, (user_id[0], user_id[0]))
        recommendations = cur.fetchall()

        # Close the cursor and connection
        cur.close()

        if not recommendations:
            return jsonify({'message': 'No hay recomendaciones disponibles para este usuario'}), 200

        return jsonify(recommendations), 200

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
        return jsonify({'error': 'Error interno del servidor'}), 500

# Endpoint to get recommendations for all users
@app.route('/recommendations')
def get_all_recommendations():
    try:
        # Create a cursor object
        cur = conn.cursor()

        # Get all users
        cur.execute("SELECT user_id FROM users")
        users = cur.fetchall()

        all_recommendations = {}

        # Iterate over users and get recommendations for each
        for user_id in users:
            cur.execute("""
                        SELECT voter_id, movie_id, movie, rating
                        FROM (
                            SELECT u.voter_id, r.movie_id, m.movie, r.rating, 
                                   ROW_NUMBER() OVER(PARTITION BY r.movie_id ORDER BY r.rating DESC) AS rn
                            FROM ratings r
                            JOIN movies m ON r.movie_id = m.movie_id
                            JOIN users u ON r.user_id = u.user_id
                            WHERE r.user_id <> %s
                            AND r.movie_id NOT IN (
                                SELECT movie_id FROM ratings WHERE user_id = %s
                            )
                        ) ranked
                        WHERE rn = 1
                        ORDER BY rating DESC
                        LIMIT 10;
                        """, (user_id[0], user_id[0]))
            recommendations = cur.fetchall()

            all_recommendations[user_id[0]] = recommendations

        # Close the cursor and connection
        cur.close()

        return jsonify(all_recommendations), 200

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
        return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
