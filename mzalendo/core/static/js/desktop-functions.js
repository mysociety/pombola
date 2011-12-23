// load all other jquery related resources
Modernizr.load(['//ajax.googleapis.com/ajax/libs/jqueryui/1.8.16/jquery-ui.min.js','//ajax.googleapis.com/ajax/libs/jqueryui/1.8/themes/base/jquery-ui.css']);

// Show a tab and hide the others. Load content from remote source if needed.
function activateSimpleTab( $heading_element ) {
    
  // Check that we have something to work with
  if ( ! $heading_element.size() ) return false

  var tab_content_id = $heading_element.attr('rel');
  var $tab_content = $(tab_content_id);

  // If this tab is already open don't open it again
  if ( $tab_content.hasClass('open') )
    return true;

  // hide any currently active tabs
  $('#tab-nav ul li.active').removeClass('active');
  $('.tab.open').removeClass('open');
  $('.tab').not('.open').hide();
  
  // Show and activate the new tab
  $heading_element.addClass('active');
  $tab_content.addClass('open').show();

  // load content using ajax if the div has an data-comment-source-url
  // TODO: use a cleaner way to specify this - probably best to have a global object and tell it that certain tabs have special opening behaviour
  var content_url = $tab_content.attr('data-comment-source-url')
  if ( content_url ) {
      $tab_content.load(content_url)
  }
  
}

//generic re-usable hide or show with class states
//todo: add states to trigger elem if provided
function hideShow(elem, trig) {
  elem.toggleClass(function() {
    if ($(this).is('.open')) {
      $(this).hide().removeClass('open');
      trig.removeClass('active');
      return 'closed';
    } else {
      $(this).show().removeClass('closed');
      trig.addClass('active');
      return 'open';
    }
  });
}


$(function(){
  /*
   * auto complete
   */
  $('#main_search_box')
    .autocomplete({
        source: "/search/autocomplete/",
        minLength: 2,
        select: function(event, ui) {
            if (ui.item) return window.location = ui.item.url;
        }
    });
    
    
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
                dialog_div.load( event.target.href + ' #ajax_dialog_subcontent' )
    
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
                dialog_div.dialog({modal: true});
    
            }
        );

  /*
   * simple tabs
   */
  // build the nav from the relavent links dotted around
  var $tabnavs = $('h2.tab-nav');
  $tabnavs.hide();
  $('.tab-wrapper').before('<div id="tab-nav"><ul></ul></div>');
  $tabnavs.each(function(){
    var rel = $(this).attr('rel');
    var txt = $(this).text();
    var href = $('a', this).attr('href');
    var newElem = '<li rel="'+rel+'"><a href="'+href+'">'+txt+'</a></li>';
    $('#tab-nav ul').append(newElem);
  }).remove();

  if(window.location.hash != '')
  {
    // get hash from url and activate it
    var hash = window.location.hash;
    $heading_element = $('li[rel='+hash+']');
    activateSimpleTab($heading_element);
  }
  else
  {
    //make initial tab active and hide other tabs
    if(!$('#tab-nav ul li').hasClass('active')){
      var simpleTabActive = $('#tab-nav ul li:first-child').attr('rel');
      $('#tab-nav ul li:first-child').addClass('active');
    }else{
      var simpleTabActive = $('#tab-nav ul li.active').attr('rel');
    }
    $(simpleTabActive).addClass('open');
    $('.tab').not('.open').hide();
  }

  //for clicks
  $("#tab-nav ul li a").click(function(e){
    e.preventDefault();
    window.location.hash = $(this).parent('li').attr('rel');
    activateSimpleTab($(this).parent('li'));
  });

  $(".tab-static-link").click(function(e){
    var hash = $(this).attr('rel');
    window.location.hash = hash;
    e.preventDefault();
    activateSimpleTab($(this));
    $("#tab-nav ul li[rel='"+hash+"']").addClass('active');
  });

  /*
   * scorecard
   */
  // prep
  $('div.details').hide();

  // hide/show details
  $('ul.scorecard article').live('click', function(){
    hideShow($('div.details', $(this)), $(this));
  });
});