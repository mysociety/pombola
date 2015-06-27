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

// process form submits without leaving the page
(function () {
  $('.inplace-form').each(function (i) {
    var form = $(this);
    /* There doesn't seem to be any particularly nice way of finding
       which submit button was clicked from jQuery's submit event.
       One way is to create a hidden input element with the submit
       button's name and value on clicking of that button, suggested
       here: http://stackoverflow.com/a/11271850/223092 */
    form.find(':submit').click(function (e) {
      if ($(this).attr('name')) {
        $(form).append(
          $('<input type="hidden">').attr({
            name: $(this).attr('name'),
            value: $(this).attr('value')
          })
        );
      }
    });
    form.on('submit', function(e) {
      var data = $(this).serialize(),
        url = this.action,
        panel = $(this).parent()[0],
        thanks = $('#' + panel.id + 'thanks');
      e.preventDefault();
      /* If this is the "support" form, make sure that the constituency
         field is set, or give an error: */
      if ($(this).attr('id') == 'support') {
        if (!$(this).find('select[name="constituencies"]').val()) {
          alert('You must select a constituency first');
          return;
        }
      }
      /* We'll post the form as an AJAX request in the background, so
         set the 'thanks' field to indicate that it's being
         submitted */
      $(panel).hide();
      $(thanks).text('Submitting your response...')
      $(thanks).show();
      $.ajax({
        url: url,
        type: 'POST',
        data: data
      }).done(function () {
        $(thanks).text('Thank-you for your input');
      }).fail(function () {
        $(thanks).text('Submission failed; you can try again');
        $(panel).show();
      });
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
