$(function() {

  // The number of people displayed on the rep locator
  // will be limited to this number, with a "Show more"
  // button beneath to reveal the rest.
  var numberOfRepsToShow = 10;

  var createMoreButton = function createMoreButton($reps){
    var $moreButton = $('<a>');
    $moreButton.addClass('button secondary-button rep-locator-reps__more');
    $moreButton.text('Show ' + ($reps.length - numberOfRepsToShow) + ' more');
    $moreButton.on('click', function(){
      $(this).nextAll().show();
      $(this).remove();
    });
    return $moreButton;
  }

  $('.rep-locator-reps').each(function(){
    var $reps = $(this).children();
    if( $reps.length > numberOfRepsToShow ){
      var $moreButton = createMoreButton($reps);
      $moreButton.insertAfter($reps.eq( numberOfRepsToShow - 1 ));
      $moreButton.nextAll().hide();
    }
  });

});
