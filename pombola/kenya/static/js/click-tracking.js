// This code opens the share or survey link in a new pop-up window.
// Since it's opened in a new window the GA event can be sent
// afterwards.

(function () {
  $.each(['.share-link', '#take-survey'], function(_, cssSelector) {
    $(cssSelector).on('click.open', function(e) {
      var label = this.id, url = this.href, width, height;
      var windowFeatures = {
        '#take-survey': 'chrome,width=800,height=600',
        '.share-link': 'chrome,width=600,height=300'
      }[cssSelector]
      e.preventDefault();
      window.open(url, label + ' window', windowFeatures);
      ga('send', 'event', {
        'eventCategory': cssSelector.substring(1),
        'eventAction': 'click',
        'eventLabel': label
      });
    });
  });
})();
