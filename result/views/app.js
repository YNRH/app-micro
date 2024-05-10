var app = angular.module("moviesApp", []);
var socket = io.connect();

app.controller("statsCtrl", function ($scope) {
  $scope.movies = [];
  $scope.total = 0;
  $scope.rating = 0;
  // Mostrar el voter_id en el título
  $scope.voter_id = getCookie("voter_id");

  // Función para obtener un cookie por nombre
  function getCookie(name) {
    var match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    if (match) return match[2];
  }

  socket.on("scores", function (json) {
    var data = JSON.parse(json);
    $scope.movies = data.movies;
    $scope.total = data.total;
    $scope.rating = data.rating;
    $scope.$apply();
  });

  socket.on("message", function (data) {
    document.body.style.opacity = 1;
  });
});
