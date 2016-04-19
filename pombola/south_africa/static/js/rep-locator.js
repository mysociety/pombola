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

  // Show the tooltip matching the given selector.
  // (If no selector provided, it defaults to the tooltip
  // matching the currently active jQuery UI tab).
  var showTooltip = function showActiveTooltip(selector){
    var selector = selector || $('.ui-tabs-active [data-rep-locator-tooltip]').attr('data-rep-locator-tooltip');
    $(selector).show().siblings('.rep-locator-tooltip').hide();
  }

  $('[data-rep-locator-tooltip]').on('mouseenter', function(){
    showTooltip( $(this).attr('data-rep-locator-tooltip') );
  }).on('mouseleave', function(){
    showTooltip();
  });

  $(".tabs").on("tabsactivate", function(event, ui) {
    showTooltip();
  });

  showTooltip();

});
