var map = undefined;
var kml_urls_to_add = [];
var markers_to_add = [];

function initialize() {
    initialize_map();
}

function initialize_map() {

    var map_element = document.getElementById("map_canvas")
    if (!map_element) return false;

    var latlng = new google.maps.LatLng(-0.023559, 37.906193);
    
    var myOptions = {
      zoom: 6,
      center: latlng,
      mapTypeId: google.maps.MapTypeId.ROADMAP,
      disableDefaultUI: true
    };

    map = new google.maps.Map(map_element, myOptions);

    // Add all the kml
    while ( kml_url = kml_urls_to_add.shift() ) {
        new google.maps.KmlLayer(
            kml_url,
            {
                map: map,
                clickable: false
            }
        );
    }

    while ( args = markers_to_add.shift() ) {

        var marker_opts = {
            position: new google.maps.LatLng(args.lat, args.lng ) ,
            title: args.name,
            map: map,
        };

        var marker = new google.maps.Marker( marker_opts );

        if ( args.url ) {
            
            var url = args.url;
            
            google.maps.event.addListener(
                marker,
                'click',
                function() {
                    window.location.replace( url );
                }
            );
        }
    }
}

function add_kml_to_map( kml_url ) {    
    kml_urls_to_add.push( kml_url );
}

function add_marker_to_map( args ) {
    markers_to_add.push(args);
}