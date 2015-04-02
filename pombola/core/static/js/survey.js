(function() {

    // Only do any of this if the survey wrapper is present
    if (document.getElementById('ms_srv_wrapper')) {

        // Get the wrapper element
        var linkWrapper = document.getElementById('ms_srv_wrapper')

        // Initialise various essentials
        var percentage = parseFloat(linkWrapper.getAttribute('data-display-percentage')),
            cookie_time = null,
            cookie_array = document.cookie.split(';'),
            i, cookie, time, site_time, link, data, query_string;

        for(i=0;i < cookie_array.length;i++) {
            cookie = cookie_array[i];
            cookie = cookie.replace(/^\s+/, '')
            if (cookie.indexOf('ms_srv_t=') == 0) {
                // Cookie for time...
                cookie_time = cookie.substring('ms_srv_t='.length,cookie.length);
            }
            if (cookie.indexOf('ms_srv_r=') == 0) {
                // Cookie for referrer...
                cookie_referrer = cookie.substring('ms_srv_r='.length,cookie.length);
            }
        }

        if (cookie_time == null) {
            // No cookie!
            if (Math.random() < percentage) {
                // Chosen to survey
                // Set the cookie to current timestamp
                time = Math.round(new Date().getTime() / 1000);
                document.cookie = 'ms_srv_t='+time+'; path=/';
                document.cookie = 'ms_srv_r='+document.referrer+'; path=/';
                cookie_time = time;
                cookie_referrer = document.referrer;

            } else {
                // Not chosen to survey
                // Set cookie to X
                document.cookie = 'ms_srv_t=X; path=/';
                cookie_time = 'X'
            }
        }

        // Only bother to do this if the cookie is not excluding the user from surveying
        if (cookie_time != 'X') {

            // Find the time on site thus far
            site_time = Math.round(new Date().getTime() / 1000) - cookie_time;

            // Find the URL on the page
            link = document.getElementById('ms_srv_link');

            data = {
                'ms_time': site_time,
                'ms_referrer': cookie_referrer || null
            }

            // Assemble the query string
            query_string = [];
            for (d in data) {
               query_string.push(encodeURIComponent(d) + "=" + encodeURIComponent(data[d]));
            }

            // Append query string to the URL
            link.href = link.href + '?' + query_string.join('&');

            // Show the survey link element
            linkWrapper.style.display = '';

            // Bind a click event to the link so we can de-survey the user
            link.onclick = function() { document.cookie = 'ms_srv_t=X; path=/'; }

        }

    }

})();
