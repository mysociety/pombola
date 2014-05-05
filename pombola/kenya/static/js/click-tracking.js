(function () {
  $.each(['.share-link', '#take-survey'], function(_, cssSelector) {
    $(cssSelector).click(function(e) {
      var label = this.id, url = this.href;
      e.preventDefault();
      ga('send', 'event', {
        'eventCategory': cssSelector.substring(1),
        'eventAction': 'click',
        'eventLabel': label,
        'hitCallback': function () {
          document.location = url;
        }
      });
    });
  });
})();
