var app = angular.module('movies', []);
var socket = io.connect();

app.controller('statsCtrl', function($scope){
  $scope.movies = [];
  $scope.totalVotes = 0;

  var updateVotes = function(){
    socket.on('votes', function (json) {
       data = JSON.parse(json);
       $scope.movies = data.movies;
       $scope.totalVotes = data.totalVotes;
    });
  };

  var init = function(){
    document.body.style.opacity=1;
    updateVotes();
  };

  socket.on('message',function(data){
    init();
  });
});

app.filter('percentage', ['$filter', function ($filter) {
    return function (input, total) {
        return total > 0 ? Math.round(input / total * 100) : 0;
    };
}]);
