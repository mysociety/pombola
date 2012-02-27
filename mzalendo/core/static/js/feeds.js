(function() {

    // Get the blog feeds - if needed
    var $blog_container = $("#home-news-list");
    if ( $blog_container ) {

        function fetch_blog_feeds () {
        
            var feed = new google.feeds.Feed("http://www.mzalendo.com/feed/");

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
                            .append( $('<p/>').text(entry.contentSnippet) );
            
            
                        $blog_container.append( $item );
                    }
                }
            });
        }

        // load the feeds API from google
        google.load('feeds', '1', { callback: fetch_blog_feeds });
    }

    // For any twitter box load the tweets
    $('.twitter-feed:visible').each( function ( index, element ) {

        var $twitter_feed = $(element);
        
        var screen_name = $twitter_feed.attr( 'data-twitter-username' );
        var feed_url = $twitter_feed.attr( 'data-feed-url' );
        
        $.ajax({
            url: feed_url,
            //url: 'http://192.168.1.32:8000/external_feeds/twitter/',
            //url: 'http://api.twitter.com/1/statuses/user_timeline.json',
            data: {
                screen_name:      screen_name,
                count:            4
            },
          //dataType: 'jsonp',
            success: function ( data, textStatus, jqXHR ) {

                $twitter_feed.html('');
                var $nub = $( '<span class="nub"></span>' );

                $.each(
                    data,
                    function( index, tweet_data ) {

                        // console.debug( tweet_data );

                        var pub_date = new Date( tweet_data.created_at );

                        var $tweet = $( '<div class="tw-wrap" />');

                        var tweet_html = $('<div/>').text( tweet_data.text ).html();

                        // make t.co links clickable
                        var http_regex = new RegExp('(http://t\.co/[a-z0-9]+)', 'gi');
                        tweet_html = tweet_html.replace( http_regex, '<a href="$1">$1</a>' );

                        // activate @names too
                        var name_regex = new RegExp('@([a-z0-9]+)', 'gi' );
                        tweet_html = tweet_html.replace( name_regex, '<a href="http://twitter.com/$1">@$1</a>' );

                        $tweet.append( $('<p/>').html( tweet_html ) );
                            
                        var tweet_url = 'http://twitter.com/' + screen_name + '/status/' + tweet_data.id_str;                        
                        $tweet.append( '<p class="meta"><a href="' + tweet_url + '">' + pub_date.toDateString() + '</a></p>');

                        $twitter_feed
                            .append($tweet)
                            .append($nub);
                    }
                );
            }
        });
    });

})();
