(function($){
    $.fn.blogFeed = function(){
        return this.each(function(){
            var $container = $(this);
            var feedURL = $container.attr('data-blog-rss-feed');
            var templateHTML = $( $container.attr('data-blog-template') ).html();
            var maxItems = parseInt($container.attr('data-blog-items')) || 2;
            var loadingTimeout;

            var dateFormat = function(dateObject) {
                var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
                var date = dateObject.getDate();
                var month = dateObject.getMonth();
                var year = dateObject.getFullYear();
                return '<span class="date">' + date +
                '</span> <span class="month">' + months[month] +
                '</span> <span class="year">' + year + '</span>';
            }

            var showLoading = function() {
                $container.empty();
                for (var i=0; i<maxItems; i++) {
                    var $el = $(templateHTML);
                    $el.find('[data-blog-title]').html(
                        greek('90%') + greek('95%') + greek('30%')
                    );
                    $el.find('[data-blog-date]').html(greek('6em'));
                    $el.find('[data-blog-description').html(
                        greek('90%') + greek('95%') + greek('85%') +
                        greek('90%') + greek('95%') + greek('30%')
                    );
                    $el.appendTo($container);
                }
            };

            var greek = function(width) {
                return '<span class="greek" style="width: ' + (width || '100%') + '"></span>';
            };

            if (feedURL && templateHTML && maxItems) {
                // We can get away with half a second of zero feedback
                // but after that, we really should show a loading state.
                loadingTimeout = setTimeout(showLoading, 500);

                $.ajax(feedURL, {dataType: 'xml'}).done(function(xml) {
                    clearTimeout(loadingTimeout);
                    $container.empty();
                    $(xml).find('item').each(function(index) {
                        if (index >= maxItems) {
                            return false; // break out of .each() loop
                        }

                        var rssItem = $(this),
                            title = rssItem.find('title').text(),
                            url = rssItem.find('link').text(),
                            description = rssItem.find('description').text(),
                            date = new Date(rssItem.find('pubDate').text()),
                            $el = $(templateHTML);

                        $el.find('[data-blog-title]').html(title);
                        $el.find('[data-blog-link]').attr('href', url);
                        $el.find('[data-blog-date]').html(dateFormat(date));
                        $el.find('[data-blog-description]').html(description);
                        $el.appendTo($container);
                    });
                }).fail(function(){
                    clearTimeout(loadingTimeout);
                });
            }
        });
    };

    $(function(){
        $('[data-blog-rss-feed]').blogFeed();
    });
})(jQuery);
