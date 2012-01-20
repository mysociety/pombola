(function() {

    // load the feeds API from google
    google.load('feeds','1', { callback: fetch_feeds });
    
    function fetch_feeds () {
        // Get the blog feeds first
        $( function() {
           
            var feed = new google.feeds.Feed("http://www.mzalendo.com/feed/atom/");
            feed.load(function(result) {
                if (!result.error) {

                    
                    var $container = $("#home-news-list");
                    $container.html('');

                    for (var i = 0; i < result.feed.entries.length; i++) {
                        var entry = result.feed.entries[i];
                        console.debug(entry);

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


                        $container.append( $item );
                    
                    
                        // var div = document.createElement("div");
                        // div.appendChild(document.createTextNode(entry.title));
                        // container.appendChild(div);
                    }
                }
            });
            
      });

        
    }

})();
