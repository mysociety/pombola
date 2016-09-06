$(function(){

    // Add the "js-hover-dropdown" class to the dropdown element
    // that should be hidden and revealed when its preceding sibling
    // is hovered or focussed.
    //
    // Example markup:
    // <ul>
    //     <li>
    //         <a href="/people">People</a>
    //         <ul class="js-hover-dropdown">
    //             <li><a href="/people/senators">Senators</a></li>
    //             <li><a href="/people/reps">Representatives</a></li>
    //         </ul>
    //     </li>
    // </ul>
    //
    // For basic cases, the hiding/showing is all handled by CSS,
    // using :hover or :focus, and the (+) next sibling selector.
    //
    // This bit of code just adds in extra niceties for users with
    // JavaScript enabled, such as touchstart support (to show the
    // dropdown on first touch, preventing navigation to the top
    // level link).

    $('.js-hover-dropdown').each(function(){
        var $dropdown = $(this);
        var $trigger = $(this).prev();
        var $parent = $(this).parent();

        // Triggers are also links to other pages. On touchscreens,
        // we want to reveal the dropdown the first time these triggers
        // are clicked, rather than following the link.
        var touch = function(e){
            if( $dropdown.is(':hidden') ){
                e.preventDefault();
                $('.js-hover-active').removeClass('js-hover-active');
                $parent.addClass('js-hover-active');
            }
        }
        $trigger.on('touchstart', touch);

        // Annoyingly, Opera Mini doesn't generate touchstart events when
        // you touch things. So in Opera Mini *only*, we bind our touch
        // shim to the click event too:
        if('operamini' in window){
            $trigger.on('click', function(e){
                // Crazily, Opera Mini *requires* us to preventDefault
                // RIGHT NOW. If we do it inside touch(), it just gets
                // ignored. (I think it's got something to do with the
                // way Opera Mini reloads the page for all interactions.)
                e.preventDefault();
                touch(e);
            });
        }

        // When dropdowns are opened by touch (instead of by hover/focus)
        // they stay open even if you click elsewhere on the page.
        // We want to close the open dropdown, when you click or press
        // outside it.
        $('body').on('click', function(){
            $('.js-hover-active').removeClass('js-hover-active');
        });
        $parent.on('click', function(e){
            e.stopPropagation();
        });

        // When a dropdown is revealed by focussing its trigger, it will
        // hide again as soon as the trigger is unfocussed. This means a
        // keyboard user can't tab from the trigger to the to the dropdown
        // contents before the dropdown is hidden. This is kinda hard to
        // solve in HTML+CSS only, but for keyboard navigation users with
        // JavaScript enabled, we can at least manually stop the dropdown
        // disappearing before it should.
        $trigger.on('focus', function(){
            $('.js-hover-active').removeClass('js-hover-active');
            $parent.addClass('js-hover-active');
        });
    });
});
