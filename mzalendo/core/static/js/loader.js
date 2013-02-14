/*
 * Test for mobile / desktop and load appropriate libs/scripts
 */
// this is not yet ideal... it reacts a bit slow if the cdn fails

(function () {
    
    var static_url = function ( path ) {
        if ( path.match('^//') )
            return path;

        return mzalendo_settings.static_url
            + path
            + '?'
            + mzalendo_settings.static_generation_number;
    };
    
    // create links to all the extra js needed
    var extra_js = [];
    for ( i=0; i<mzalendo_settings.extra_js.length; i++ ) {
        var extra = mzalendo_settings.extra_js[i];
        var url = static_url( extra );
        extra_js.push( url );
    }
        
    Modernizr.load(
        {
            test : Modernizr.mq('only all and (max-width: 640px)'),
            yep : [
                static_url('js/libs/zepto-0.8.min.js'),
                static_url('js/mobile-functions.js')
            ],
            nope : [
                static_url('js/libs/jquery-1.7.1.min.js'),
                static_url('js/libs/jquery-ui-1.8.17.custom.min.js'),
                static_url('js/libs/jquery.ui.autocomplete.html.2010-10-25.js'),
                static_url('js/libs/jquery.form-v2.94.js'), // TODO - only load when needed for feedback form                    
                static_url('js/desktop-functions.js'),                
            ],
            both: [
                static_url('js/both-functions.js'),
                '//www.google.com/jsapi' // ?key=INSERT-YOUR-KEY
            ].concat( extra_js ),
            complete: function () {
                for (i=0; i<mzalendo_run_when_document_ready_array.length; i++) {
                    $( mzalendo_run_when_document_ready_array[i] );
                }

                // Now load all the optional bits that we didn't want slowing down the more important bits
                Modernizr.load([
                  static_url('js/analytics.js')
                  // ,
                  // '//platform.twitter.com/widgets.js',
                  // '//connect.facebook.net/en_GB/all.js#xfbml=1&appId=' + mzalendo_settings.facebook_app_id
                ]);
            }
        }
    );
})();

var mzalendo_run_when_document_ready_array = [];

function mzalendo_run_when_document_ready (func) {
    if ( window.$ ) {
        $(func);
    } else {
        mzalendo_run_when_document_ready_array.push( func );
    }
}
