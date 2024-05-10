# recommendation_service.py
import psycopg2
from math import sqrt

# Conexión a la base de datos PostgreSQL
conn = psycopg2.connect(
    dbname="DBmovies",
    user="postgres",
    password="postgres",
    host="db"
)
cur = conn.cursor()

def manhattan(rating1, rating2):
    """Calcula la distancia de Manhattan entre dos conjuntos de calificaciones."""
    distance = 0
    commonRatings = False
    for movie in rating1:
        if movie in rating2:
            distance += abs(rating1[movie] - rating2[movie])
            commonRatings = True
    if commonRatings:
        return distance
    else:
        return -1  # Indica que no hay calificaciones en común

def computeNearestNeighbor(username, users):
    """Crea una lista ordenada de usuarios basada en su distancia a username."""
    distances = []
    for user in users:
        if user != username:
            distance = manhattan(users[user], users[username])
            distances.append((distance, user))
    # Ordena según la distancia -- más cercano primero
    distances.sort()
    return distances

def recommend(username, users):
    """Da una lista de recomendaciones."""
    # Encuentra primero al vecino más cercano
    nearest = computeNearestNeighbor(username, users)[0][1]

    recommendations = []
    # Encuentra las películas que el vecino ha calificado pero el usuario no
    neighborRatings = users[nearest]
    userRatings = users[username]
    for movie in neighborRatings:
        if movie not in userRatings:
            recommendations.append((movie, neighborRatings[movie]))
    # Usando la función sorted para variedad - sort es más eficiente
    return sorted(recommendations, key=lambda movieTuple: movieTuple[1], reverse=True)

def generate_recommendations_for_new_user():
    """Genera recomendaciones para un nuevo usuario."""
    # Datos estáticos de los usuarios y sus calificaciones para las películas
    users = {
        "User1": {"Inception": 4, "The Shawshank Redemption": 3, "The Godfather": 5, "The Dark Knight": 2,
                  "Pulp Fiction": 1, "Forrest Gump": 4, "The Matrix": 3, "The Lord of the Rings": 5},
        # Agrega más usuarios y sus calificaciones aquí
    }

    # Nuevo usuario con sus calificaciones de películas
    new_user = {
        "NewUser": {"Inception": 4, "The Shawshank Redemption": 5, "The Godfather": 3, "The Dark Knight": 2}
    }

    # Ejemplo de recomendaciones para el nuevo usuario
    recommendations = recommend('NewUser', users)
    return recommendations

if __name__ == "__main__":
    recommendations = generate_recommendations_for_new_user()
    print("Recomendaciones para el nuevo usuario:")
    for movie, rating in recommendations:
        print(f"{movie}: {rating}")
