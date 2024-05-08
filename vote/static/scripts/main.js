$(document).ready(function () {
  $(".rating-button").click(function () {
    var movie = $(this).attr("name");
    var value = $(this).attr("value");
    $("button[name='" + movie + "']").removeClass("selected");
    $(this).addClass("selected");
    $(this).siblings().prop("disabled", false);
    $(this).prop("disabled", true);
    $("button[name='" + movie + "']").html(function () {
      return $(this).attr("value");
    });
  });
});
