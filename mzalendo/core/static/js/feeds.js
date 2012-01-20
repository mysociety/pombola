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

})();
