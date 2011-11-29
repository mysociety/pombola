Modernizr.load(['//ajax.googleapis.com/ajax/libs/jqueryui/1.8.16/jquery-ui.min.js','//ajax.googleapis.com/ajax/libs/jqueryui/1.8/themes/base/jquery-ui.css']);

// tabs
function simpleTabs(elem)
{
  var tc = elem.attr('rel');
  if(!$(tc).hasClass('open'))
  {
    //hide/show tab content
    $('#tab-nav ul li.active').removeClass('active');
    $(elem).addClass('active');
    $('.tab.open').removeClass('open').hide();
    $(tc).addClass('open').show();
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
  alert('woo');
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
    //strip out default active states
    $('#tab-nav ul li.active').removeClass('active');

    //get hash from url
    var hash = window.location.hash;
    $('#tab-nav ul').find("li[rel='"+hash+"']").addClass('active');

    //make the hashed tab active and hide all others
    var simpleTabActive = $('#tab-nav ul li.active').attr('rel');
    $(simpleTabActive).addClass('open');
    $('.tab').not('.open').hide();
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
    simpleTabs($(this).parent('li'));
  });

  $(".tab-static-link").click(function(e){
    var hash = $(this).attr('rel');
    window.location.hash = hash;
    e.preventDefault();
    simpleTabs($(this));
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