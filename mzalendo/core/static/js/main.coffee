# enable the autocomplete on main search box
$ ->
    $('#main_search_box').autocomplete
        source: "/autocomplete"
        minLength: 2
        select: ( event, ui ) ->
        	window.location = ui.item.url if ui.item
