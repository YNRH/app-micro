var express = require('express'),
    async = require('async'),
    path = require('path'),
    { Pool } = require('pg'),
    cookieParser = require('cookie-parser'),
    app = express(),
    server = require('http').Server(app),
    io = require('socket.io')(server);

var port = process.env.PORT || 4000;

io.on('connection', function (socket) {

  socket.emit('message', { text : 'Welcome!' });

  socket.on('subscribe', function (data) {
    socket.join(data.channel);
  });
});

var pool = new Pool({
  connectionString: 'postgres://postgres:postgres@db/postgres'
});

async.retry(
  {times: 1000, interval: 1000},
  function(callback) {
    pool.connect(function(err, client, done) {
      if (err) {
        console.error("Waiting for db");
      }
      callback(err, client);
    });
  },
  function(err, client) {
    if (err) {
      return console.error("Giving up");
    }
    console.log("Connected to db");
    getVotes(client);
  }
);

function getVotes(client) {
  client.query('SELECT vote, COUNT(id) AS count FROM votes GROUP BY vote', [], function(err, result) {
    if (err) {
      console.error("Error performing query: " + err);
    } else {
      var votes = collectVotesFromResult(result);
      var movies = votes.movies.map(movie => movie.name);
      // Emitting the list of movies to the users
      io.sockets.emit("votes", JSON.stringify(votes));
      // Emitting the list of recommended movies
      io.sockets.emit("recommendations", JSON.stringify(recommendations(movies)));
    }

    setTimeout(function() {getVotes(client) }, 1000);
  });
}

function collectVotesFromResult(result) {
  var movies = [];
  var totalVotes = 0;

  result.rows.forEach(function (row) {
    var movie = { name: row.vote, votes: parseInt(row.count) };
    movies.push(movie);
    totalVotes += movie.votes;
  });

  movies.sort((a, b) => b.votes - a.votes);

  return { movies: movies.slice(0, 4), totalVotes: totalVotes };
}

// Recommendations based on user votes
function recommendations(userMovies) {
  var userMoviesSet = new Set(userMovies);
  var recommendations = [];
  for (var user in users) {
    var nearest = computeNearestNeighbor(user, users)[0][1];
    var neighborRatings = users[nearest];
    for (var movie in neighborRatings) {
      if (!userMoviesSet.has(movie)) {
        recommendations.push({ name: movie, score: neighborRatings[movie] });
      }
    }
  }
  return recommendations.sort((a, b) => b.score - a.score).slice(0, 4);
}

app.use(cookieParser());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(__dirname + '/views'));

app.get('/', function (req, res) {
  res.sendFile(path.resolve(__dirname + '/views/index.html'));
});

server.listen(port, function () {
  var port = server.address().port;
  console.log('App running on port ' + port);
});

