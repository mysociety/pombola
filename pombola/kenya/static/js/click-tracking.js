// This code opens the share link in a new pop-up window.  Since it's
// opened in a new window the GA event can be sent afterwards.

(function () {
  $.each(['.share-link'], function(_, cssSelector) {
    $(cssSelector).on('click.open', function(e) {
      var label = this.id, url = this.href;
      e.preventDefault();
      window.open(url, label + ' window', 'chrome,width=600,height=300');
      ga('send', 'event', {
        'eventCategory': cssSelector.substring(1),
        'eventAction': 'click',
        'eventLabel': label
      });
    });
  });
})();

// Open the survey link in the same window; in this case we need to
// only go to the URL after the GA event has been recorded, so use
// hitCallback for that.

(function () {
  $('#take-survey').click(function(e) {
    var label = this.id, url = this.href;
    e.preventDefault();
    ga('send', 'event', {
      'eventCategory': 'take-survey',
      'eventAction': 'click',
      'eventLabel': label,
      'hitCallback': function () {
        $('#survey-form').submit()
      }
    });
  });
})();
