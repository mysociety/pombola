/*
 * Test for mobile / desktop and load appropriate libs/scripts
 */
// this is not yet ideal... it reacts a bit slow if the cdn fails

(function () {
    
    var static_url = function ( path ) {
        return mzalendo_settings.static_url
            + path
            + '?'
            + mzalendo_settings.static_generation_number;
    };
    
    var post_jquery_desktop_load = [
        '//ajax.googleapis.com/ajax/libs/jqueryui/1.8.16/jquery-ui.min.js',
        static_url('js/libs/jquery.form-v2.94.js'), // TODO - only load when needed for feedback form
        static_url('js/desktop-functions.js')
    ];
    
    var are_we_on_a_mobile = Modernizr.mq('only screen and (min-width: 320px) and (max-width: 640px)');

    Modernizr.load([
        {
            test : are_we_on_a_mobile,
            yep : [
                static_url('js/libs/zepto-0.8.min.js'),
                static_url('js/mobile-functions.js')
            ],
            nope : '//ajax.googleapis.com/ajax/libs/jquery/1.7.0/jquery.min.js',
            complete: function () {
                // only run this if mq failed - e.g. desktop or no mq support (IE)
                if( ! are_we_on_a_mobile ) {
                    // test for jquery
                    if ( !window.jQuery ) {
                        // not downloaded from CDN, so get local
                        Modernizr.load([
                            {
                                load : static_url('js/libs/jquery-1.7.0.min.js'),
                                complete : function () {
                                    // once local has been fetched, check for jQuery object again and load static libs and functions if there
                                    if ( window.jQuery ) {
                                        Modernizr.load( post_jquery_desktop_load );
                                    }
                                }
                            }
                        ]);
                    }else{
                        // if jQuery object is there, load in the rest of the static libs and functions
                        Modernizr.load( post_jquery_desktop_load );
                    }
                }
            }
        },
        {
            load: [
                '//platform.twitter.com/widgets.js',
                static_url('js/analytics.js'),
                static_url('js/fb-like.js')
            ]
        }
    ]);
})();
