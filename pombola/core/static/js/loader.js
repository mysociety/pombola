/*
 * Test for mobile / desktop and load appropriate libs/scripts
 */
// this is not yet ideal... it reacts a bit slow if the cdn fails

(function () {
    
    // create links to all the extra js needed
    var extra_js = [];
    for ( i=0; i<pombola_settings.extra_js.length; i++ ) {
        var extra = pombola_settings.extra_js[i], url;
        if (extra) {
            extra_js.push(extra);
        }
    }
        
    Modernizr.load(
        {
            test : Modernizr.mq('only all and (max-width: 640px)'),
            yep : [
                '//ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js',
            ].concat(pipeline_mobile_only),
            nope : [
                '//ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js',
            ].concat(pipeline_desktop_only),
            both: pipeline_desktop_and_mobile.concat(
                ['//www.google.com/jsapi']),
            complete: function () {
                $(function() {
                    for (i=0; i<pombola_run_when_document_ready_array.length; i++) {
                        $( pombola_run_when_document_ready_array[i] );
                    }
                    Modernizr.load(extra_js.concat(pipeline_analytics));
                });
            }
        }
    );
})();
