$(function() {
  $('#appearances')
    .html("Loading&hellip;&hellip;")
    .each( function () {
      var appearances = $(this);
      var url = appearances.data('url');
      appearances.load(url);
    });
});
