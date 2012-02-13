/*
 * Height fix for pages with .profile-info box
 */
function profileInfoHeightFix() {
  var pro_h = $('.profile-info').height()+210; //add 210 for the profile pic
  var main_h = $('#page .page-wrapper').height();

  if(pro_h > main_h){
    $('#page .page-wrapper').css({'min-height':pro_h});
  }
}


// Show a tab and hide the others. Load content from remote source if needed.
function activateSimpleTab( $heading_element ) {
    
  // Check that we have something to work with
  if ( ! $heading_element.size() ) return false;

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

  // load content using ajax if the div has an data-tab-content-source-url
  // TODO: use a cleaner way to specify this - probably best to have a global object and tell it that certain tabs have special opening behaviour
  var content_url = $tab_content.attr('data-tab-content-source-url');
  if ( content_url ) {
      $tab_content.load(content_url);
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
    $('input.search-autocomplete-name')
    .autocomplete({
        source: "/search/autocomplete/",
        minLength: 2,
        select: function(event, ui) {
            if (ui.item) return window.location = ui.item.url;
        }
    });
    
    // hide/show home intro
    $('.home-read-more').on('click', function(){
      hideShow($('#home-intro span.details'), $(this));
      if($('.home-read-more.active').length !== 0){
        $(this).text('less');
      }else{
        $(this).text('more');
      }
    });
    
    // auto-advance cycles through featured MPs; it also immediately replaces the
    // featured MP in the page (since we assume that has been frozen by caching)
    var auto_advance_enabled = true;
    var init_auto_advance_delay = 12000;
    var auto_advance_delay = init_auto_advance_delay;
    
    function transitionDiv(height) {
      return '<div class="featured-person featured-person-loading" style="height:' +
        + height + 'px"><p>loading...</p></div>';      
    }

    // featured-person prev and next clicks: for now, we only have this in one place, so use id
    // broken out as a function so it can re-invent itself on load
    // note: any click stops autoadvance (by setting delay to zero)
    function enableFeaturedPersonNav() {
      $('.feature-nav > a', '#home-featured-person').click(
        function(e){
          e.preventDefault();
          auto_advance_delay = 0;
          var m = $(this).attr('href').match(/(before|after)=([-\w]+)$/);
          if (m.length==3) { // wee sanity check: found direction [1] and slug [2]
            $('#home-featured-person')
              .html(transitionDiv($('#home-featured-person').height()))
                .load(
                  "person/featured/" + m[1] + '/' + m[2],
                  function() {
                    enableFeaturedPersonNav();
                  }
                );
          }
        }
      );
    }
    
    enableFeaturedPersonNav();
    if (auto_advance_enabled) {
      $('#home-featured-person').html(transitionDiv(30)).load(
          'person/featured/' + Math.floor(Math.random()*900), 
          function(){enableFeaturedPersonNav();
      });
      var timer = window.setTimeout(auto_advance, auto_advance_delay);
      function auto_advance(){
        if (auto_advance_delay > 0){
          $('a.feature-next', '#home-featured-person').click();
          auto_advance_delay = init_auto_advance_delay;
          timer = window.setTimeout(auto_advance, auto_advance_delay);
        }
      }
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

  /*
   * simple tabs
   */

  // build the nav from the relavant links dotted around
  var $tabnavs = $('h2.tab-nav');
  $tabnavs.hide();
  $('.tab-wrapper').before('<div id="tab-nav"><ul></ul></div>');
  $tabnavs.each(function(){
    var rel = $(this).attr('rel');
    var txt = $(this).text();
    var href = $('a', this).attr('href');
    var aClass  = $(this).hasClass('tab-static-link')? 'class="tab-static-link"':'';
    var liClass = $(this).hasClass('tab-active')? 'tab-active':'';
    var newElem = '<li rel="'+rel+'" class="tab-nav-heading ' + liClass + '"><a href="'+href+'" '+aClass+'>'+txt+'</a></li>';
    $('#tab-nav ul').append(newElem);
  }).remove();

  // store the matched element from the hash here:
  // first look to see if it's already been marked server-side (tab-active)
  var matched_element = $('li.tab-active').first();

  // If not already active, if there is a hash try to load from that
  if(! matched_element.length && window.location.hash !== '') {
    var hash = window.location.hash;
    matched_element = $('li[rel='+hash+']');
  }

  // If there was no hash, or it didn't match, use the first one
  if ( ! matched_element.length ) {
    matched_element = $('li.tab-nav-heading').first();
  }
  
  // activate the tab
  activateSimpleTab(matched_element);
  profileInfoHeightFix();

  //for clicks
  $("#tab-nav ul li a").not(".tab-static-link").click(function(e){
    e.preventDefault();
    window.location.hash = $(this).parent('li').attr('rel');
    activateSimpleTab($(this).parent('li'));
    profileInfoHeightFix();
  });

  // $(".tab-static-link").click(function(e){
  //   var hash = $(this).attr('rel');
  //   window.location.hash = hash;
  //   e.preventDefault();
  //   activateSimpleTab($(this));
  //   $("#tab-nav ul li[rel='"+hash+"']").addClass('active');
  // });

  /*
   * scorecard
   */
  // prep
  $('div.details').hide();

  // hide/show details
  $('ul.scorecard article.has-details').live('click', function(){
    hideShow($('div.details', $(this)), $(this));
  });

  /*
   * Comments: hover and show tools
   */
  $('.comments li').hover(function() {
    $(this).addClass('hovered');
  },
  function() {
    $(this).removeClass('hovered');
  });


  /*
   * Login box
   */
  var login_target = $('#site-user-tools .login a').attr('href');

  $('#site-user-tools').after('<div id="login-box">Loading...</div>');
  

  $('li.login').on('click', function(event) {
    event.preventDefault();
    $('#login-box').load(login_target + ' #login');
    hideShow($('#login-box'), $(this));
  });

  /*
   * Main nav hover
   */
  $('#main-menu ul > li').on('mouseover', function(){
    if($(this).children('ul').length === 1){
      // alert('oh yeah');
      $(this).addClass('active');
    }
  }).on('mouseout', function(){
    $(this).removeClass('active');
  });
  
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