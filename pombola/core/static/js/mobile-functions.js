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

$(function(){
  /*
   * General stuff
   */
  //hide url bar on ios / android
  hideUrlBar();
  // add appropriate stuff to head
  // <!-- Mobile viewport optimization http://goo.gl/b9SaQ -->
  $('head').append('<meta name="HandheldFriendly" content="True">').append('<meta name="MobileOptimized" content="320">');

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