(function($){
    $.fn.featuredPerson = function(){
        return this.each(function(){
            var $container = $(this);
            var placeholderImageUrl = $container.data('placeholder-image-url');
            var loadingTimeout;

            var loadFeaturedPerson = function(url){
                var m = url.match(/(before|after)=([-\w]+)$/);
                if ( m.length === 3 ) { // found direction [1] and slug [2]
                    var originalHTML = $container.html();

                    // We can get away with half a second of zero feedback
                    // but after that, we really should show a loading state.
                    loadingTimeout = setTimeout(showLoading, 500);

                    $.get('person/featured/' + m[1] + '/' + m[2]).always(function(){
                        clearTimeout(loadingTimeout);
                    }).done(function(html){
                        $container.html(html);
                    }).fail(function(){
                        $container.html(originalHTML);
                    });
                }
            };

            var showLoading = function() {
                $container.find('img').replaceWith('<div class="greek-img"></div>');
                $container.children('a').removeAttr('href');
                $container.find('h3').html(greek('60%'));
                $container.find('.homepage-featured-person__role').html(greek('6em'));
                $container.find('.homepage-featured-person__description').html(
                    greek('90%') + greek('95%') + greek('85%') + greek('30%')
                );
            };

            var greek = function(width) {
                return '<span class="greek" style="width: ' + (width || '100%') + '"></span>';
            }

            $container.on('click', 'header a', function(e){
                e.preventDefault();
                loadFeaturedPerson( $(this).attr('href') );
            });
        });
    };

    $(function(){
        $('.js-featured-person').featuredPerson();
    });
})(jQuery);
