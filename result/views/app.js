var app = angular.module("moviesApp", []);
var socket = io.connect();

app.controller("moviesController", function ($scope, $http) {
  // Define API_URL
  //$scope.API_URL = 'http://api:5002';

  var init = function () {
    document.body.style.opacity = 1;
  };
  socket.on("message", function (data) {
    init();
  });

  // Función para obtener la cookie "voter_id" del navegador
  function getCookie(name) {
    var value = "; " + document.cookie;
    var parts = value.split("; " + name + "=");
    if (parts.length == 2) return parts.pop().split(";").shift();
  }

  // Obtener el voter_id
  $scope.voter_id = getCookie("voter_id");

  // Obtener las recomendaciones para el usuario
  if ($scope.voter_id) {
    $http.get('http://localhost:5002/recommendations/' + $scope.voter_id)
    .then(function (response) {
      console.log('Datos de respuesta de la API:', response.data);
      $scope.recomendaciones = response.data;
      $scope.total_recomendadas = response.data.length;
    })
    .catch(function (error) {
      console.log('Error al obtener recomendaciones:', error);
    });
  }
});
