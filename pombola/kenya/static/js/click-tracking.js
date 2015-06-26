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

// track clicks on links without leaving the page
(function () {
  $.each(['.inplace-link'], function(_, cssSelector) {
    $(cssSelector).on('click.open', function(e) {
      url = this.href;
      e.preventDefault();
      // call the thanks page in the background
      $.ajax({
        url: url,
        type: 'get',
      });
      // hide the panel with the link buttons
      // unhide the pre-prepared thankyou panel
      panel = $(this).parent()[0];
      $(panel).hide();
      thanks = $('#' + panel.id + 'thanks');
      $(thanks).show()
      if (navigator.userAgent.indexOf('Opera Mini') > -1) {
        $(document).scrollTop(thanks.offsetTop);
      }
    });
  });
})();

// process form submits without leaving the page
(function () {
  $.each(['.inplace-form'], function(_, cssSelector) {
    $(cssSelector).on('submit', function(e) {
      data = $(this).serialize();
      e.preventDefault();
      url = this.action;
      // post the form in the background
      $.ajax({
        url: url,
        type: 'POST',
        data: data
      });
      // hide the panel with the form
      // unhide the pre-prepared thankyou panel
      panel = $(this).parent()[0];
      $(panel).hide();
      thanks = $('#' + panel.id + 'thanks');
      $(thanks).show();
      if (navigator.userAgent.indexOf('Opera Mini') > -1) {
        $(document).scrollTop(thanks.offsetTop);
      }
    });
  });
})();

// Opera Mini specific fix for video scaling
(function () {
  $.each(['.embedded-video'], function(_, cssSelector) {
    if (navigator.userAgent.indexOf('Opera Mini') > -1) {
      $(cssSelector).find('.ratio-img').hide();
    }
  });
})();