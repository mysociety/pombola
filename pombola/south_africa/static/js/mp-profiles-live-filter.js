var setUpFilterer = function setUpFilterer(){
    var reps = [];
    $('.person-list-item').each(function(){
        reps.push({
            el: this,
            name: $(this).find('.name').text()
        });
    });

    return new Fuse(reps, {
        shouldSort: true,
        threshold: 0.5,
        location: 0,
        distance: 64,
        maxPatternLength: 32,
        minMatchCharLength: 1,
        keys: [ "name" ],
        include: [ "score", "matches" ]
    });
};

var hideFilterResults = function hideFilterResults(){
    $('.js-filter-results').remove();
    $('.js-mp-profiles-all').show();
};

var showFilterResults = function showFilterResults(){
    $('.js-mp-profiles-all').hide();

    var $results = $('.js-filter-results');

    if($results.length){
        $results.empty();
    } else {
        $results = $('<ul>').addClass('unstyled-list mp-profiles-list js-filter-results');
        $results.insertBefore('.js-mp-profiles-all');
    }

    return $results;
};

var filterProfiles = function filterProfiles(searchTerm, filterer){
    if(searchTerm === ''){
        return hideFilterResults();
    }

    var results = filterer.search(searchTerm);

    if(results.length === 0){
        return hideFilterResults();
    }

    var $results = showFilterResults();

    $.each(results, function(i, result){
        var $clone = $(result.item.el).clone();
        $clone.appendTo($results);
    });

    // Other scripts might want to do something special once they know
    // new person-list-items have been added (eg: might want to check
    // the viewport for new images to be lazy-loaded).
    $(document).trigger('js-mp-profiles-live-filter:updated');
};

$(function(){
    var filterer = setUpFilterer();

    // Ideally, we only want to update the search state when the search input
    // text has been changed, ignoring other keystrokes like Ctrl-A / Ctrl-C.
    // Modern browsers and IE9+ support the `input` event. But some old
    // browsers like IE8 don't. So we provide `keyup` as a fallback.
    var filterInputEvent = 'input';
    if(jQuery.support && jQuery.support.input === false){
      filterInputEvent = 'keyup';
    }

    $('.js-mp-profiles-live-filter').on(filterInputEvent, function(){
        filterProfiles(
            $(this).val(),
            filterer
        );
    }).parents('form').on('submit', function(e){
        e.preventDefault();
        filterProfiles(
            $('.js-mp-profiles-live-filter').val(),
            filterer
        );
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
