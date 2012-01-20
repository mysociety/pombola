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
        
    Modernizr.load(
        {
            test : Modernizr.mq('only screen and (min-width: 320px) and (max-width: 640px)'),
            yep : [
                static_url('js/libs/zepto-0.8.min.js'),
                static_url('js/mobile-functions.js')
            ],
            nope : [
                static_url('js/libs/jquery-1.7.1.min.js'),
                static_url('js/libs/jquery-ui-1.8.17.custom.min.js'),
                static_url('js/libs/jquery.form-v2.94.js'), // TODO - only load when needed for feedback form                    
                static_url('js/desktop-functions.js'),                
            ],
            both: [
                '//platform.twitter.com/widgets.js',
                static_url('js/analytics.js'),
                static_url('js/fb-like.js')
            ]
        }
    );

})();
