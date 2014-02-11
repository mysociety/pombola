var map = undefined;
var kml_urls_to_add = [];
var markers_to_add = [];

function initialize_map() {

    var map_element = document.getElementById("map_canvas")
    if (!map_element) return false;


    var bound_coords = window.pombola_settings.map_bounds;
    var map_bounds = new google.maps.LatLngBounds(
      new google.maps.LatLng( bound_coords.south, bound_coords.west ),
      new google.maps.LatLng( bound_coords.north, bound_coords.east )
    );

    var map_has_been_located = false;

    var myOptions = {
      mapTypeId: google.maps.MapTypeId.ROADMAP,
      disableDefaultUI: true,
      maxZoom: 16
    };

    map = new google.maps.Map(map_element, myOptions);

    if (markers_to_add.length) {

        // clear the bounds so that they are set from markers
        var map_bounds = new google.maps.LatLngBounds();

        while ( args = markers_to_add.shift() ) {

            var position = new google.maps.LatLng(args.lat, args.lng );

            var marker_opts = {
                position: position,
                title: args.name,
                map: map,
            };

            if (args.marker_icon) {
              marker_opts.icon = args.marker_icon;
            }

            // set the bounds to accomodate this marker
            map_bounds.extend(position);

            var marker = new google.maps.Marker( marker_opts );

            if ( args.url ) {
                set_marker_click_url( marker, args.url );
            }
        }
    }

    // Add all the kml
    while ( kml_url = kml_urls_to_add.shift() ) {
        map.setOptions({ maxZoom: 16 }); // allow zooming on kml
        new google.maps.KmlLayer(
            kml_url,
            {
                map: map,
                clickable: false
            }
        );
        map_has_been_located = true;
    }

    if ( ! map_has_been_located ) {
        map.fitBounds( map_bounds );
    }

}

// done as a seperate function so the the url variable is respected in the closure.
function set_marker_click_url ( marker, url) {
    google.maps.event.addListener(
        marker,
        'click',
        function() { window.location = url; }
    );
}

function add_kml_to_map( kml_url ) {
    kml_urls_to_add.push( kml_url );
}

function add_marker_to_map( args ) {
    markers_to_add.push(args);
}

pombola_run_when_document_ready(
    function () {
        google.load(
            'maps', '3',
            {
                callback: initialize_map,
                other_params:'sensor=false'
            }
        );
    }
);
