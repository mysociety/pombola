$(function(){
  /*
   * auto complete
   */
    $('input.search-autocomplete-name')
    .each(function(){
      var element = $(this);
      var source = element.data('source') || "/search/autocomplete/";
      element.autocomplete({
          source: source,
          minLength: 2,
          html: true,
          select: function(event, ui) {
              if (ui.item) return window.location = ui.item.url;
          }
      });
      element.data('uiAutocomplete')._renderItem = function(ul, item) {
          var itemElement = $('<li>'), imageElement = $('<img>');
          imageElement.attr('src', item.image_url);
          imageElement.attr('width', '16');
          imageElement.attr('height', '16');
          itemElement.append(imageElement).append(' ' + item.name);
          if (item.extra_data) {
              itemElement.append(' ').append($('<i>').append(item.extra_data));
          }
          return itemElement.appendTo(ul);
      };
    });

    // auto-advance cycles through featured MPs; it also immediately replaces the
    // featured MP in the page (since we assume that has been frozen by caching)
    var auto_advance_enabled = false;
    var auto_advance_delay = 12000; // milliseconds
    var auto_advance_timeout = false;

    function transitionDiv(height) {
      return '<div class="featured-person featured-person-loading" style="height:'
        + $('#home-featured-person').height() + 'px"><p>loading...</p></div>';
    }

    $('.js-expanded-toggle').on('click', function(e){
      e.preventDefault();
      if ( $(this).attr('aria-expanded') === 'true' ) {
        $(this).attr('aria-expanded', false);
      } else {
        $(this).attr('aria-expanded', true);
      }
    });

    // important to delegate this (with on()) because the contents change each auto-advance
    $('#home-featured-person').on("click", '.feature-nav > a', function(e, is_auto_advancing){
      e.preventDefault();
      if (! is_auto_advancing) { // user clicked
        auto_advance_enabled = false;
        if (auto_advance_timeout) {
          clearTimeout(auto_advance_timeout);
        }
      }

      var m = $(this).attr('href').match(/(before|after)=([-\w]+)$/);
      if (m.length==3) { // wee sanity check: found direction [1] and slug [2]
        $('#home-featured-person .featured-person').replaceWith( transitionDiv() );
        $.get("person/featured/" + m[1] + '/' + m[2]).done(function(html){
          $('#home-featured-person .featured-person').replaceWith(html);
        });
      }
    });

    if (auto_advance_enabled) {
      $('#home-featured-person .featured-person').replaceWith( transitionDiv() );
      $.get('person/featured/' + Math.floor(Math.random()*100)).done(function(html){
        // some random index of featured person
        $('#home-featured-person .featured-person').replaceWith(html);
      });
      function auto_advance(){
        if (auto_advance_enabled){
          $('#home-featured-person a.feature-next').trigger("click", true);
          auto_advance_timeout = window.setTimeout(auto_advance, auto_advance_delay);
        }
      }
      auto_advance_timeout = window.setTimeout(auto_advance, auto_advance_delay);
    }

    /*
     * enable dialog based feedback links
     */
      $('a.feedback_link')
        .on(
            'click',
            function(event) {
                // Note - we could bail out here if the window is too small, as
                // we'd be on a mobile and it might be better just to send them to
                // the feedback page. Not done as this js should only be loaded on
                // a desktop.

                // don't follow the link to the feedback page.
                event.preventDefault();

                // create a div to use in the dialog
                var dialog_div = $('<div>Loading...</div>');

                // Load the initial content for the dialog
                dialog_div.load( event.target.href + ' #ajax_dialog_subcontent' );

                // Form subission should be done using ajax, and only the ajax_dialog_subcontent should be shown.
                var handle_form_submission = function( form_submit_event ) {
                    form_submit_event.preventDefault();
                    var form = $(form_submit_event.target);
                    form.ajaxSubmit({
                        success: function( responseText ) {
                            dialog_div.html( $(responseText).find('#ajax_dialog_subcontent') );
                        }
                    });
                };

                // catch all form submissions and do them using ajax
                dialog_div.on( 'submit', 'form', handle_form_submission );

                // Show the dialog
                dialog_div.dialog({
                  modal: true,
                  minHeight: 320,
                  width: 500,
                  title: 'Leave Feedback'
                });

            }
        );

  /* carry search terms across when switching between search pages */
  $("#search-hansard-instead").click(function(e){
    e.preventDefault();
    location.href="/search/hansard?q=" + escape($('#core-search,#id_q,#loc').first().val());
  });
  $("#search-core-instead").click(function(e){
    e.preventDefault();
    location.href="/search?q=" + escape($('#id_q,#loc').first().val());
  });
});
