// Worker/Program.cs
using System;
using System.Data.Common;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using Newtonsoft.Json;
using Npgsql;
using StackExchange.Redis;

namespace Worker
{
    public class Program
    {
        public static int Main(string[] args)
        {
            try
            {
                var pgsql = OpenDbConnection("Server=db;Username=postgres;Password=postgres;Database=DBmovies;");
                var redisConn = OpenRedisConnection("redis");
                var redis = redisConn.GetDatabase();

                // Keep alive is not implemented in Npgsql yet. This workaround was recommended:
                // https://github.com/npgsql/npgsql/issues/1214#issuecomment-235828359
                var keepAliveCommand = pgsql.CreateCommand();
                keepAliveCommand.CommandText = "SELECT 1";

                while (true)
                {
                    // Slow down to prevent CPU spike, only query each 100ms
                    Thread.Sleep(100);

                    // Reconnect redis if down
                    if (redisConn == null || !redisConn.IsConnected)
                    {
                        Console.WriteLine("Reconnecting Redis");
                        redisConn = OpenRedisConnection("redis");
                        redis = redisConn.GetDatabase();
                    }

                    // Retrieve all keys from Redis matching the pattern "user_ratings:*"
                    var keys = redis.Multiplexer.GetServer(redisConn.GetEndPoints()[0]).Keys(pattern: "user_ratings:*");

                    foreach (var key in keys)
                    {
                        // Get user_id from the key
                        var userId = key.ToString().Split(':')[1];

                        // Get all fields and values from the hash
                        var hashEntries = redis.HashGetAll(key);

                        foreach (var hashEntry in hashEntries)
                        {
                            var movie = hashEntry.Name.ToString();
                            var ratingJson = hashEntry.Value.ToString();

                            // Deserialize JSON to anonymous type
                            var rating = JsonConvert.DeserializeAnonymousType(ratingJson, new { movie = "", rating = 0 });

                            Console.WriteLine($"Processing rating for '{rating.movie}'");
                            // Insert rating into PostgreSQL
                            InsertRating(pgsql, userId, rating.movie, rating.rating);
                        }

                        // After processing, remove the key from Redis
                        redis.KeyDelete(key);
                    }

                    // Execute keep alive command to prevent connection timeout
                    keepAliveCommand.ExecuteNonQuery();
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine(ex.ToString());
                return 1;
            }
        }

        private static NpgsqlConnection OpenDbConnection(string connectionString)
        {
            NpgsqlConnection connection;

            while (true)
            {
                try
                {
                    connection = new NpgsqlConnection(connectionString);
                    connection.Open();
                    break;
                }
                catch (SocketException)
                {
                    Console.Error.WriteLine("Waiting for db");
                    Thread.Sleep(1000);
                }
                catch (DbException)
                {
                    Console.Error.WriteLine("Waiting for db");
                    Thread.Sleep(1000);
                }
            }

            Console.Error.WriteLine("Connected to db");

            var command = connection.CreateCommand();
            command.CommandText = @"CREATE TABLE IF NOT EXISTS users (
                                        user_id SERIAL PRIMARY KEY,
                                        voter_id VARCHAR(255) UNIQUE,
                                        name VARCHAR(255)
                                    );

                                    CREATE TABLE IF NOT EXISTS movies (
                                        movie_id SERIAL PRIMARY KEY,
                                        movie VARCHAR(255) UNIQUE
                                    );

                                    CREATE TABLE IF NOT EXISTS ratings (
                                        rating_id SERIAL PRIMARY KEY,
                                        user_id INT REFERENCES users(user_id),
                                        movie_id INT REFERENCES movies(movie_id),
                                        rating INT NOT NULL
                                    )";
            command.ExecuteNonQuery();

            return connection;
        }

        private static ConnectionMultiplexer OpenRedisConnection(string hostname)
        {
            // Use IP address to workaround https://github.com/StackExchange/StackExchange.Redis/issues/410
            var ipAddress = GetIp(hostname);
            Console.WriteLine($"Found redis at {ipAddress}");

            while (true)
            {
                try
                {
                    Console.Error.WriteLine("Connecting to redis");
                    return ConnectionMultiplexer.Connect(ipAddress);
                }
                catch (RedisConnectionException)
                {
                    Console.Error.WriteLine("Waiting for redis");
                    Thread.Sleep(1000);
                }
            }
        }

        private static string GetIp(string hostname)
            => Dns.GetHostEntryAsync(hostname)
                .Result
                .AddressList
                .First(a => a.AddressFamily == AddressFamily.InterNetwork)
                .ToString();

        private static void InsertRating(NpgsqlConnection connection, string userId, string movie, int rating)
        {
            var command = connection.CreateCommand();
            try
            {
                // Insert user if not exists
                command.CommandText = "INSERT INTO users (voter_id) VALUES (@userId) ON CONFLICT (voter_id) DO NOTHING RETURNING user_id";
                command.Parameters.AddWithValue("@userId", userId);
                var userIdObj = command.ExecuteScalar();
                int userIdInt;
                if (userIdObj == null)
                {
                    command.CommandText = "SELECT user_id FROM users WHERE voter_id = @userId";
                    userIdObj = command.ExecuteScalar();
                    userIdInt = Convert.ToInt32(userIdObj);
                }
                else
                {
                    userIdInt = Convert.ToInt32(userIdObj);
                }

                // Insert movie if not exists
                command.CommandText = "INSERT INTO movies (movie) VALUES (@movie) ON CONFLICT (movie) DO NOTHING RETURNING movie_id";
                command.Parameters.Clear();
                command.Parameters.AddWithValue("@movie", movie);
                var movieIdObj = command.ExecuteScalar();
                int movieId;
                if (movieIdObj == null)
                {
                    command.CommandText = "SELECT movie_id FROM movies WHERE movie = @movie";
                    movieIdObj = command.ExecuteScalar();
                    movieId = Convert.ToInt32(movieIdObj);
                }
                else
                {
                    movieId = Convert.ToInt32(movieIdObj);
                }

                // Check if the user has already rated the movie
                command.CommandText = "SELECT COUNT(*) FROM ratings WHERE user_id = @userId AND movie_id = @movieId";
                command.Parameters.Clear();
                command.Parameters.AddWithValue("@userId", userIdInt);
                command.Parameters.AddWithValue("@movieId", movieId);
                var existingRatingCount = Convert.ToInt32(command.ExecuteScalar());

                if (existingRatingCount > 0)
                {
                    // If the user has already rated the movie, update the rating
                    command.CommandText = "UPDATE ratings SET rating = @rating WHERE user_id = @userId AND movie_id = @movieId";
                    command.Parameters.Clear();
                    command.Parameters.AddWithValue("@rating", rating);
                    command.Parameters.AddWithValue("@userId", userIdInt);
                    command.Parameters.AddWithValue("@movieId", movieId);
                    command.ExecuteNonQuery();
                }
                else
                {
                    // If the user has not rated the movie before, insert a new rating
                    command.CommandText = "INSERT INTO ratings (user_id, movie_id, rating) VALUES (@userId, @movieId, @rating)";
                    command.Parameters.Clear();
                    command.Parameters.AddWithValue("@userId", userIdInt);
                    command.Parameters.AddWithValue("@movieId", movieId);
                    command.Parameters.AddWithValue("@rating", rating);
                    command.ExecuteNonQuery();
                }
            }
            catch (DbException)
            {
                // Handle duplicate ratings if necessary
                Console.WriteLine($"Rating for '{movie}' already exists in the database.");
            }
            finally
            {
                command.Dispose();
            }
        }


    }
}

