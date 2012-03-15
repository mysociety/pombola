$( function () {
    
    // When we are on a mobile we should show and hide the posts when the title is clicked
    $('div.post h2 a').on( 'click', function ( e ) {

        if ( Modernizr.mq('only screen and (max-width: 639px)') ) {

            // find the post containing the link
            var $post = $(this).closest('div.post');
            
            // use toggle, slideToggle not available in Zepto which is what the mobiles load
            $post.find( 'section' ).toggle();
            $post.find( 'p.comments-link' ).toggle();

            // Don't follow the click
            e.preventDefault();
        }
        
    });
    
});