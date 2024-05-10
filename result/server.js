var express = require("express"),
  async = require("async"),
  { Pool } = require("pg"),
  cookieParser = require("cookie-parser"),
  path = require("path"),
  app = express(),
  server = require("http").Server(app),
  io = require("socket.io")(server);

var port = process.env.PORT || 4000;

io.on("connection", function (socket) {
  socket.emit("message", { text: "Welcome!" });

  socket.on("subscribe", function (data) {
    socket.join(data.channel);
  });
});

var pool = new Pool({
  connectionString: "postgres://postgres:postgres@db/DBmovies",
});

// Mantén un mapeo de sockets y voter_id
var socketMap = {};

io.on("connection", function (socket) {
  socket.emit("message", { text: "Welcome!" });

  socket.on("subscribe", function (data) {
    socket.join(data.channel);
  });

  // Asocia el voter_id con el socket
  socket.on("set_voter_id", function (data) {
    var voter_id = data.voter_id;
    socketMap[voter_id] = socket;
  });
});

async.retry(
  { times: 1000, interval: 1000 },
  function (callback) {
    pool.connect(function (err, client, done) {
      if (err) {
        console.error("Waiting for db");
      }
      callback(err, client);
    });
  },
  function (err, client) {
    if (err) {
      return console.error("Giving up");
    }
    console.log("Connected to db");
    io.on("connection", function (socket) {
      // Asocia el voter_id con el socket
      var voter_id = socket.request.headers.cookie
        .split("; ")
        .find((row) => row.startsWith("voter_id="))
        .split("=")[1];
      socketMap[voter_id] = socket;

      // Llama a getVotes con el voter_id
      getVotes(client, voter_id);
    });
  }
);

// Función para obtener los votos de la base de datos
function getVotes(client, voter_id) {
  client.query(
    "SELECT r.movie, COUNT(*) AS count, AVG(r.rating) AS rating FROM ratings r INNER JOIN users u ON r.user_id = u.user_id WHERE u.voter_id = $1 GROUP BY r.movie ORDER BY rating DESC",
    [voter_id],
    function (err, result) {
      if (err) {
        console.error("Error performing query: " + err);
      } else {
        var ratings = collectRatingsFromResult(result);
        // Emitir solo al socket asociado con el voter_id
        var socket = socketMap[voter_id];
        if (socket) {
          socket.emit("scores", JSON.stringify(ratings));
        }
      }

      setTimeout(function () {
        getVotes(client, voter_id);
      }, 1000);
    }
  );
}

// Función para recopilar las calificaciones de las películas desde el resultado de la consulta
function collectRatingsFromResult(result) {
  var ratings = {
    movies: [],
    total: 0,
  };

  result.rows.forEach(function (row) {
    var movie = {
      name: row.movie,
      count: parseInt(row.count),
      rating: parseFloat(row.rating),
    };
    ratings.movies.push(movie);
    ratings.total += parseInt(row.count);
  });

  return ratings;
}

app.use(cookieParser());
app.use(express.urlencoded());
app.use(express.static(__dirname + "/views"));

app.get("/", function (req, res) {
  res.sendFile(path.resolve(__dirname + "/views/index.html"));
});

server.listen(port, function () {
  var port = server.address().port;
  console.log("App running on port " + port);
});
