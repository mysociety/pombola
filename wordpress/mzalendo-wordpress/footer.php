            </div> <!-- close .page-wrapper -->
        </div> <!-- close #page -->

        <footer id="site-footer">
            <div class="wrapper">
                <ul class="nav">
                    <li><a href="http://info.mzalendo.com/person/all/">People</a></li>
                    <li><a href="http://info.mzalendo.com/organisation/all/">Organisations</a></li>
                    <li><a href="http://info.mzalendo.com/place/all/">Places</a></li>
                </ul>

                <ul class="utilities">
                    <li><a href="http://info.mzalendo.com/info/policies/">Privacy</a></li>
                    <li><a href="http://info.mzalendo.com/feedback/" class="feedback_link">Give us feedback</a></li>
                </ul>

                <div class="subscribe-box">
                    <h2>Email Newsletter</h2>

                    <form action="http://mzalendo.us2.list-manage.com/subscribe/post?u=c0b4940a102336a932a5c30c4&amp;id=9963e6377d" method="post" id="mc-embedded-subscribe-form" name="mc-embedded-subscribe-form" class="validate" target="_blank">
                        <label for="mce-EMAIL">Subscribe to recieve updates</label>
                        <div class="subscribe-fields">
                            <input type="email" value="" name="EMAIL" class="email" id="mce-EMAIL" placeholder="Your email address here" required>
                            <input type="submit" value="Subscribe" name="subscribe" id="mc-embedded-subscribe" class="button">
                        </div>
                    </form>
                </div>
            </div>
        </footer>
        <script type="text/javascript">
            /*
             * Test for mobile / desktop and load appropriate libs/scripts
             */
            // this is not yet ideal... it reacts a bit slow if the cdn fails

            //define global vars
            window.mzalendo_settings = {
                analytics_id : 'UA-660910-5',
                facebook_app_id: '315517795130516'
            }

            var post_jquery_desktop_load = [
                '//ajax.googleapis.com/ajax/libs/jqueryui/1.8.16/jquery-ui.min.js',
                'http://info.mzalendo.com/static/js/libs/jquery.form-v2.94.js', // TODO - only load when needed for feedback form
                'http://info.mzalendo.com/static/js/desktop-functions.js'
            ];

            Modernizr.load([
                {
                    test : Modernizr.mq('only screen and (min-width: 320px) and (max-width: 640px)'),
                    yep : ['http://info.mzalendo.com/static/js/libs/zepto-0.8.min.js', 'http://info.mzalendo.com/static/js/mobile-functions.js', '<?php bloginfo('template_url'); ?>/assets/js/wp-mobile-functions.js'],
                    nope : '//ajax.googleapis.com/ajax/libs/jquery/1.7.0/jquery.min.js',
                    complete: function () {
                        // only run this if mq failed - e.g. desktop or no mq support (IE)
                        if(Modernizr.mq('only screen and (min-width: 320px) and (max-width: 640px)') === false) {
                            // test for jquery
                            if ( !window.jQuery ) {
                                // not downloaded from CDN, so get local
                                Modernizr.load([
                                    {
                                        load : 'http://info.mzalendo.com/static/js/libs/jquery-1.7.0.min.js',
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
                    load: ['//platform.twitter.com/widgets.js', 'http://info.mzalendo.com/static/js/analytics.js', 'http://info.mzalendo.com/static/js/fb-like.js']
                }
            ]);
        </script>
        <div id="fb-root"></div>
        <?php // wp_footer(); ?>
    </body>
</html>