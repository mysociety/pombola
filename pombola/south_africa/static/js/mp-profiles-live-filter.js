(function ($) {
    $.fn.containsText = function(searchFor) {
        var found = false;
        this.each(function() {
            if( $(this).text().toUpperCase().indexOf(searchFor.toUpperCase()) > -1 ){
                found = true;
            }
        });
        return found;
    }
}(jQuery));

var filterProfiles = function filterProfiles(searchTerm){
    if(searchTerm === ''){
        $('.person-list-item--hidden').removeClass('person-list-item--hidden');
        $('.mp-profiles-list-letter--hidden').removeClass('mp-profiles-list-letter--hidden');

    } else {
        $('.list-of-profiles-by-letter').each(function(){
            var $items = $(this).children();
            var hiddenItems = 0;

            $items.each(function(){
                if( $('.name', $(this)).containsText(searchTerm) ){
                    $(this).removeClass('person-list-item--hidden');
                } else {
                    $(this).addClass('person-list-item--hidden');
                    hiddenItems += 1;
                }
            });

            // Hide the big alphabet letter, if all the profiles
            // in this section have been hidden.
            var $letter = $(this).prev('.mp-profiles-list-letter');
            if( $items.length === hiddenItems ){
                $letter.addClass('mp-profiles-list-letter--hidden');
            } else {
                $letter.removeClass('mp-profiles-list-letter--hidden');
            }
        });
    }

    // Other scripts might want to do something special once they know
    // the page has been filtered (eg: might want to check the viewport
    // for new images to be lazy-loaded).
    $(document).trigger('js-mp-profiles-live-filter:updated');
};

$(function(){
    // Ideally, we only want to update the search state when the search input
    // text has been changed, ignoring other keystrokes like Ctrl-A / Ctrl-C.
    // Modern browsers and IE9+ support the `input` event. But some old
    // browsers like IE8 don't. So we provide `keyup` as a fallback.
    var filterInputEvent = 'input';
    if(jQuery.support && jQuery.support.input === false){
      filterInputEvent = 'keyup';
    }

    $('.js-mp-profiles-live-filter').on(filterInputEvent, function(){
        filterProfiles( $(this).val() );
    });

    // If device is short, and search input is in bottom half of the screen
    // when it is focussed, scroll the search input to top of the screen.
    // Handy for very short windows, or devices with on-screen keyboards,
    // where live filter results would normally get hidden offscreen.
    $('.js-mp-profiles-live-filter').on('focus', function(){
        var inputBottomEdge = $(this).offset().top + $(this).outerHeight();
        var windowMidpoint = $(window).scrollTop() + (window.innerHeight / 2);
        if(
            window.innerHeight < 800 &&
            inputBottomEdge > windowMidpoint
        ){
            $('html, body').animate({
                scrollTop: $(this).parents('form').offset().top - 10
            }, 250);
        }
    });
});
