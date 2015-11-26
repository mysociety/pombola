$(function() {
  $(".tabs").tabs();
  $(".tabs").on("tabsactivate", function(event, ui) {
    history.pushState(null, null, '#' + ui.newPanel[0].id);
  });
});
