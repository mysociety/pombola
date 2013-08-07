// Mobile boilerplate helper function (https://github.com/h5bp/mobile-boilerplate/blob/master/js/mylibs/helper.js)
// Hide URL Bar for iOS and Android by Scott Jehl
// https://gist.github.com/1183357
function hideUrlBar() {
  var win = window,
    doc = win.document;

  // If there's a hash, or addEventListener is undefined, stop here
  if( !location.hash || !win.addEventListener ){

    //scroll to 1
    window.scrollTo( 0, 1 );
    var scrollTop = 1,

    //reset to 0 on bodyready, if needed
    bodycheck = setInterval(function(){
      if( doc.body ){
        clearInterval( bodycheck );
        scrollTop = "scrollTop" in doc.body ? doc.body.scrollTop : 1;
        win.scrollTo( 0, scrollTop === 1 ? 0 : 1 );
      } 
    }, 15 );

    win.addEventListener( "load", function(){
      setTimeout(function(){
        //reset to hide addr bar at onload
        win.scrollTo( 0, scrollTop === 1 ? 0 : 1 );
      }, 0);
    }, false );
  }
}


//generic re-usable hide or show with class states
function hideShow(elem, trig) {
  $(elem).toggleClass(function() {
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
   * General stuff
   */
  //hide url bar on ios / android
  hideUrlBar();
  // add appropriate stuff to head
  // <!-- Mobile viewport optimization http://goo.gl/b9SaQ -->
  $('head').append('<meta name="HandheldFriendly" content="True">').append('<meta name="MobileOptimized" content="320">');

  /*
   * Main non AJAX interactions
   */
  // prep
  $('#mc-embedded-subscribe-form').hide();


  // news letter subscribe
  $('.subscribe-box > h2').on('click', function(){
    hideShow('#mc-embedded-subscribe-form', $(this));
  });

  /*
   * Get the sub-menu links if on a page with child items
   */
  //if .page-title has a data-sub-menu-id attr
  //clone the relavent ul#data-sub-menu-id from in the menu
  //stick below .page-title
  //show button inside .page-title that toggles the ul#data-sub-menu-id
  var sub_menu_id = '#'+$('.page-title').attr('data-sub-menu-id'),
      $page_title = $('.page-title');
  if($(sub_menu_id).length !== 0){
    $page_title.addClass('has-sub-menu').append('<button class="m-sub-menu-trigger">Show sub menu</button>');
    $(sub_menu_id).hide().insertAfter($page_title).addClass('m-sub-menu');
  }

  $('.m-sub-menu-trigger').on('click', function(e){
    e.preventDefault();
    hideShow(sub_menu_id, $(this));
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