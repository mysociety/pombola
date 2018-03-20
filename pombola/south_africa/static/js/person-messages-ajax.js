$(function(){
    var messagesSelector = '.js-person-messages-all';

    $('.js-person-messages-ajax').each(function() {
        var $tab = $(this);
        var $panel = $($tab.attr('href'));
        var url = $tab.data('ajax-url');
        $.ajax({
            url: url
        }).done(function(html) {
            $panel.html( $(html).find(messagesSelector) );
        }).fail(function() {
            $panel.html('<p>Error: Unable to load messages at this time. Please try again later.</p>');
        });
    });
});
