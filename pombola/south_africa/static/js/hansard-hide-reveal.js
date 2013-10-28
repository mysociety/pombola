$(document).ready(function() {
    $(".js-hansard-section").hide();






});

//rough around the edges sharing links reveal
$(".js-hansard-section-title").click(function(e) {

  e.preventDefault();

  //Toggle an element and close any others that are open
  var section = $(this).next(".js-hansard-section").slideToggle(200);



});