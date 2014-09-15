/**
 * Collapse sections then reveal them when an associated link is clicked.
 *
 * - Each section should have the class `js-hide-reveal`
 * - Each section should have an id attribute
 * - Links that open a section should have the class `js-hide-reveal-link`
 * - Each links' href attribute should specify the id of the section to reveal.
 */
(function($) {

    /**
     * Event handler which hides or reveals the element referred to
     * by the event target's href attribute.
     *
     * @param {jQuery.Event} e The jQuery event object
     */
    var hideOrRevealHref = function(e) {
        e.preventDefault();
        var $this = $(this);
        $($this.attr('href')).slideToggle(200);
    };

    var revealAllHref = function (e) {
      e.preventDefault();
      $('.js-hide-reveal').show();
    };

    $(document).ready(function() {
        $('.js-hide-reveal').hide();
        $('.js-hide-reveal-link').click(hideOrRevealHref);
        $('.js-reveal-all-link').click(revealAllHref);
    });

})(jQuery);
