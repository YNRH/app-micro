$(document).ready(function () {
  // Función para manejar el clic en los botones de calificación
  $(".rating-button").click(function () {
    var movie = $(this).attr("name"); // Obtener el nombre de la película
    var value = $(this).attr("value"); // Obtener el valor de la calificación

    // Si el botón ya tiene la clase 'selected', se deselecciona
    if ($(this).hasClass("selected")) {
      $(this).removeClass("selected"); // Remover la clase 'selected'
      $(this).siblings().prop("disabled", false); // Habilitar todos los botones de calificación
      $(this).html(value); // Restaurar el valor original del botón
    } else {
      // Si el botón no tiene la clase 'selected', se selecciona
      // Remover la clase 'selected' de todos los botones de la película
      $("button[name='" + movie + "']").removeClass("selected");
      $(this).addClass("selected"); // Agregar la clase 'selected' al botón actual
      $(this).siblings().prop("disabled", false); // Habilitar todos los botones de calificación
      $(this).prop("disabled", true); // Deshabilitar el botón actual
      $(this).html(value); // Mostrar el valor de la calificación en el botón
    }
  });

  // Función para enviar el formulario de manera asíncrona
  $("#submit-btn").click(function () {
    var formData = new FormData();
    $(".movie").each(function () {
      var movieName = $(this).find("h4").text();
      var rating = $(this).find(".rating-button.selected").attr("value");
      if (rating) {
        formData.append(movieName, rating);
      }
    });

    $.ajax({
      type: "POST",
      url: "/",
      data: formData,
      processData: false,
      contentType: false,
      success: function (response) {
        console.log('¡Calificaciones enviadas correctamente!');
      },
      error: function (error) {
        console.log('Error al enviar las calificaciones. Inténtalo de nuevo.');
      },
    });
  });
});
