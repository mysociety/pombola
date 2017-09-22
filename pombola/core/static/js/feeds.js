(function() {

    var dateFormat = function(dateObject){
        var days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
        var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        var day = dateObject.getDay();
        var date = dateObject.getDate();
        var month = dateObject.getMonth();
        var year = dateObject.getFullYear();
        return '<span class="day">' + days[day] +
          '</span> <span class="month">' + months[month] +
          '</span> <span class="date">' + date +
          '</span> <span class="year">' + year + '</span>';
    }

    // This Javascript will populate a <ul> with list items from an
    // RSS feed. The remote site that serves the RSS should include
    // CORS headers to allow this Javascript to fetch the RSS feed.

    var blogContainer = $("#home-news-list");
    var maximumListItems = 2;
    if ( blogContainer ) {
        var feedURL = blogContainer.attr("data-blog-rss-feed");
        $.ajax(feedURL, {dataType: 'xml'}).done(
            function (xml) {
                blogContainer.html('');
                $(xml).find('item').each(function (index) {
                    var item = $(this),
                        listItem = $('<li>'),
                        title = item.find('title').text(),
                        url = item.find('link').text(),
                        description = item.find('description').text(),
                        published = new Date(item.find('pubDate').text());
                    if (index >= maximumListItems) {
                        return false;
                    };
                    listItem.append(
                        $('<a>').text(title).attr({href: url}).wrap('<h3></h3>').parent()
                    ).append(
                        $('<p>').addClass('meta').html(dateFormat(published))
                    ).append(
                        $('<p>').html(description)
                    );
                    blogContainer.append(listItem);
                })
            }
        );
    }

})();
