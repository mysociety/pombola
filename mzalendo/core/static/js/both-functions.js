// In the ${object}_base.html templates there are menus linking to the subpages.
// It proved to be difficult to elegantly get these to render differently on
// each page so that the current page link was not a link, or muted. Mainly this
// was because to avoid repeating complicated if locks in the templates I wanted
// to use an include to generate the li element. But that meant passing in the
// name of the page to load for {% url foo ...%} and that can't take foo as a
// variable until Django 1.5. Sigh.
//
// Hence writing a teeny bit of js to do it instead.
$(function () {

  $('div.object_menu')
    .find('a')
    .each(function () {
      var $link = $(this);
      var href = $link.attr('href').replace(/\#.*$/, '');

      if ( href == window.location.pathname ) {
        // make it look less like a link, but keep it a link so that the
        // padding etc does not change.
        $link.css({
          color:          'inherit',
          textDecoration: 'none'
        });
      }

    });
});
