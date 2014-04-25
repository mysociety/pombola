(function () {
    $('.share-link').click(function(e) {
        var match = this.id.match(/^share-(.*)$/), url = this.href;
        e.preventDefault();
        if (match)  {
            ga('send', 'event', {
                'eventCategory': 'share-link',
                'eventAction': 'click',
                'eventLabel': match[1],
                'hitCallback': function () {
                    document.location = url;
                }
            });
        }
    });
})();
