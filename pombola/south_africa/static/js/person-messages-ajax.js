$(function(){
    var messagesSelector = '.js-person-messages-all';

    $('.js-person-messages-ajax').each(function() {
        var $tab = $(this);
        var $tabsWidget = $tab.parents('.ui-tabs');
        var url = $tab.data('ajax-url');

        // Ajax the message list the first time that this tab is activated.
        // You can't bind to the "activate" event of a single tab, so we
        // listen for *all* activations in this tab's parent widget, and
        // only act if it's the right tab, and the message list content
        // hasn't already been ajaxed in.
        $tabsWidget.on("tabsbeforeactivate", function(event, ui) {
            var activatingThisTab = $('a', ui.newTab).is($tab);
            var contentNotYetLoaded = $(messagesSelector, ui.newPanel).length == 0;

            if ( activatingThisTab && contentNotYetLoaded ) {
                $.ajax({
                    url: url
                }).done(function(html) {
                    ui.newPanel.html( $(html).find(messagesSelector) );
                }).fail(function() {
                    // Something went wrong with ajax. Fallback to page load.
                    location.href = url;
                });
            }
        });
    });
});
