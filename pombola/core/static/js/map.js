var map = undefined;
var map_loaded_callbacks = [];

var added_kml_layers = []
var added_markers = []

function remove_kml_layers() {
  while (layer = added_kml_layers.shift()) {
    layer.setMap(null);
  }
}

function remove_markers() {
  while (marker = added_markers.shift()) {
    marker.setMap(null);
  }
}

function add_kml_urls(kml_urls_to_add) {
  var layer, i, kml_url;
  map.setOptions({ maxZoom: 16 });
  for (i = 0; i < kml_urls_to_add.length; ++i) {
    kml_url = kml_urls_to_add[i];
    layer = new google.maps.KmlLayer(
      kml_url,
      {
        map: map,
        clickable: false
      }
    );
    added_markers.push(layer);
  }
}

function add_markers(markers_to_add) {
  var marker_opts,
    // clear the bounds so that they are set from markers
    map_bounds = new google.maps.LatLngBounds(),
    i, marker_data;

  for (i = 0; i < markers_to_add.length; ++i)  {
    marker_data = markers_to_add[i];

    var position = new google.maps.LatLng(marker_data.lat, marker_data.lng);

    marker_opts = {
      position: position,
      title: marker_data.name,
      map: map,
    };

    if (marker_data.marker_icon) {
      marker_opts.icon = marker_data.marker_icon;
    }

    // set the bounds to accomodate this marker
    map_bounds.extend(position);

    var marker = new google.maps.Marker(marker_opts);
    added_markers.push(marker);

    if (marker_data.url) {
      set_marker_click_url(marker, marker_data.url);
    }
  }
  map.fitBounds( map_bounds );
}

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
      maxZoom: 16,
      zoomControl: true,
      zoomControlOptions: {
        style: google.maps.ZoomControlStyle.SMALL
      }
    };

    map = new google.maps.Map(map_element, myOptions);

    google.maps.event.addListenerOnce(map, 'idle', function(){
        var i, callback;
        for (i = 0; i < map_loaded_callbacks.length; i++) {
            map_loaded_callbacks[i](map);
        }
    });

    if (typeof markers_to_add !== "undefined" && markers_to_add.length) {
        add_markers(markers_to_add);
        while (markers_to_add.length) {
          markers_to_add.pop();
        }
        map_has_been_located = true;
    }

    // Add all the kml
    if (typeof kml_urls_to_add !== "undefined" && kml_urls_to_add.length) {
        add_kml_urls(kml_urls_to_add);
        while (kml_urls_to_add.length) {
            kml_urls_to_add.pop();
        }
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

$(function () {
        google.load(
            'maps', '3',
            {
                callback: initialize_map,
                other_params:'key=AIzaSyCsI0iDUA5waenMFVuinV6dciKwkgaqQt8'
            }
        );
    }
);
