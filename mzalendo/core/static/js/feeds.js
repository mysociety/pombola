(function() {

    // Get the blog feeds - if needed
    var $blog_container = $("#home-news-list");
    if ( $blog_container ) {

        function fetch_blog_feeds () {
        
            var feed = new google.feeds.Feed("http://www.mzalendo.com/feed/atom/");

            feed.load(function(result) {
                if (!result.error) {
            
                    
                    $blog_container.html('');
            
                    for (var i = 0; i < result.feed.entries.length; i++) {
                        var entry = result.feed.entries[i];
            
                        var pub_date = new Date(entry.publishedDate);
            
                        var $item = $('<li />');
                        $item
                            .append(
                                $('<h3 >')
                                    .append(
                                        $('<a/>')
                                            .text( entry.title )
                                            .attr( { href: entry.link } )
                                    )
                            )
                            .append( '<p class="meta">' + pub_date.toDateString() + '</p>')
                            .append( '<p>' + entry.contentSnippet + '</p>' );
            
            
                        $blog_container.append( $item );
                    }
                }
            });
        }

        // load the feeds API from google
        google.load('feeds', '1', { callback: fetch_blog_feeds });
    }

    // For any twitter box load the tweets
    $('.twitter-feed').each( function ( index, element ) {

        var $twitter_feed = $(element);
        
        var screen_name = $twitter_feed.attr( 'data-twitter-username' );
        
        $.ajax({
            url: 'https://api.twitter.com/1/statuses/user_timeline.json',
            data: {
                screen_name:      screen_name,
                count:            4
            },
            dataType: 'jsonp',
            success: function ( data, textStatus, jqXHR ) {

                $twitter_feed.html('');
                var $nub = $( '<span class="nub"></span>' );

                $.each(
                    data,
                    function( index, tweet_data ) {

                        var pub_date = new Date( tweet_data.created_at );

                        var $tweet = $( '<div class="tw-wrap" />');
                        $tweet
                            .append( '<p>' + tweet_data.text + '</p>' )
                            .append( '<p class="meta">' + pub_date.toDateString() + '</p>');

                        $twitter_feed
                            .append($tweet)
                            .append($nub);
                    }
                );
            }
        });
    });

})();
