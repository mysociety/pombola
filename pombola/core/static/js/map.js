var map = undefined;
var kml_urls_to_add = [];
var markers_to_add = [];

function initialize_map() {

    var map_element = document.getElementById("map_canvas")
    if (!map_element) return false;

    var map_bounds = {
      north: window.pombola_settings.map_bounds.north,
      east:  window.pombola_settings.map_bounds.east,
      south: window.pombola_settings.map_bounds.south,
      west:  window.pombola_settings.map_bounds.west
    };

    var map_has_been_located = false;

    var myOptions = {
      mapTypeId: google.maps.MapTypeId.ROADMAP,
      disableDefaultUI: true,
      maxZoom: 10
    };

    map = new google.maps.Map(map_element, myOptions);

    if (markers_to_add.length) {

        // clear the bounds so that they are set from markers
        map_bounds = {
            north: -80, south: 80,
            east: -179, west: 179,
        };

        while ( args = markers_to_add.shift() ) {

            var marker_opts = {
                position: new google.maps.LatLng(args.lat, args.lng ) ,
                title: args.name,
                map: map,
            };

            // set the bounds to accomodate this marker
            if (map_bounds.north < args.lat) map_bounds.north = args.lat;
            if (map_bounds.south > args.lat) map_bounds.south = args.lat;
            if (map_bounds.east < args.lng)  map_bounds.east  = args.lng;
            if (map_bounds.west > args.lng)  map_bounds.west  = args.lng;

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
        map.fitBounds( make_bounds( map_bounds ) );
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

function make_bounds ( bounds ) {
    var sw = new google.maps.LatLng( bounds.south, bounds.west );
    var ne = new google.maps.LatLng( bounds.north, bounds.east );
    return new google.maps.LatLngBounds( sw, ne );
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
