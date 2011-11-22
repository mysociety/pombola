// enable the autocomplete on main search box
$(
    function() {
        $('#main_search_box').autocomplete({
            source: "/autocomplete",
            minLength: 2,
            select: function( event, ui ) {
            	if ( ui.item ) {
                    window.location = ui.item.url;
            	}
            }
        })
    }
)
