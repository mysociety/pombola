(function($){
    $.fn.smsCarousel = function(){
        return this.each(function(){
            var $pagination = $(this);
            var $carousel = $( $pagination.data('sms-carousel') );
            var messagesPerPage = $carousel.children().length;

            var constructMessageElement = function(message) {
                var $newMessage = $carousel.children().eq(0).clone();
                $newMessage.find('p').eq(0).html(message.content);
                $newMessage.find('footer p').eq(0).html(message.date);
                return $newMessage;
            };

            var loadPage = function(pageIndex) {
                var newMessages = window.sms_all_messages.slice(
                    messagesPerPage * pageIndex,
                    messagesPerPage * (pageIndex + 1)
                );
                // We need to keep the old message elements around while we construct
                // new ones, to save messy HTML templating. But by caching a selection
                // here, we can easily delete all the $oldMessages when we’re done.
                var $oldMessages = $carousel.children();
                $.each(newMessages, function(i, message){
                    constructMessageElement(message).appendTo($carousel);
                });
                $oldMessages.remove();
                $pagination.find('[disabled]').removeAttr('disabled');
                $pagination.find('[value="' + pageIndex + '"]').attr('disabled', true);
            };

            $pagination.find('button').on('click', function(e){
                if (window.sms_all_messages.length) {
                    e.preventDefault();
                    loadPage( parseInt($(this).val()) );
                }
            });
        });
    };

    $(function(){
        $('[data-sms-carousel]').smsCarousel();
    });
})(jQuery);
