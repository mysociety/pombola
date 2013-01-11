(function () {

  function initialize_map() {

    var map_element = document.getElementById("map-drilldown-canvas");
    if (!map_element) return false;

    // start with the default bounds for kenya
    var map_bounds = {
      north: 5, 
      east:  44,
      south: -5,
      west:  33.5
    };

    var map_has_been_located = false;

    var myOptions = {
      mapTypeId: google.maps.MapTypeId.TERRAIN,
      maxZoom: 10
    };

    var map = new google.maps.Map(map_element, myOptions);

    map.fitBounds( make_bounds( map_bounds ) );

    // Add crosshairs at the center - see merging of answers at 
    // http://stackoverflow.com/questions/4130237
    var crosshairs_path = window.mzalendo_settings.static_url + 'images/crosshairs.png?' + window.mzalendo_settings.static_generation_number 

    var reticleImage = new google.maps.MarkerImage(
       crosshairs_path,                 // marker image
       new google.maps.Size(63, 63),    // marker size
       new google.maps.Point(0,0),      // marker origin
       new google.maps.Point(32, 32)    // marker anchor point
    );
    
    var reticleShape = {
      coords: [32,32,32,32],           // 1px
      type: 'rect'                     // rectangle
    };
    
    var reticleMarker = new google.maps.Marker({
      map: map,
      icon: reticleImage
    });
    
    reticleMarker.bindTo('position', map, 'center');
    

    // react to changes in the map
    google.maps.event.addListener(
      map,
      'center_changed',
      function () { updateLocation( map.getCenter() ); }
    );
    
  }
  
  function reducePrecision (val) {
    var precision = 100;
    return Math.round(val * precision ) / precision;
  };

  function updateLocation (latlng) {

      var lat = reducePrecision( latlng.lat() );
      var lng = reducePrecision( latlng.lng() );

      fetchAreas( lat, lng, displayAreas );
  } 


  // Get the areas hash from the server, or the local cache. Debounce as well
  // so that we don't issue too many requests during map movements.

  var fetchAreasCurrentRequest  = null;
  var fetchAreasDebounceTimeout = null;
  var fetchAreasCurrentURL      = null;
  var fetchAreasCache           = {};

  function fetchAreas ( lat, lng ) {

    var mapitPointURL = '/mapit/point/4326/' + lng + ',' + lat;
    console.log(lat, lng, mapitPointURL);

    // Check that we are not at the current location already
    if (mapitPointURL == fetchAreasCurrentURL) {
      return;
    }
    fetchAreasCurrentURL = mapitPointURL;

    // clear current request and timeout
    clearTimeout(fetchAreasDebounceTimeout);
    if (fetchAreasCurrentRequest) {
      fetchAreasCurrentRequest.abort();
    }

    // Check to see if we have this result in cache already
    if (fetchAreasCache[mapitPointURL]) {
      displayAreas( fetchAreasCache[mapitPointURL] );
      return;
    }

    // Not in cache - fetch from server
    fetchAreasDebounceTimeout = setTimeout(
      function () {
        fetchAreasCurrentRequest = $.get( mapitPointURL, function (data) {
          fetchAreasCache[mapitPointURL] = data;
          displayAreas(data);
        } );         
      },
      1000
    );  
  }
  
  function displayAreas (areas) {
    var messageHolder = $('#map-drilldown-message');
    messageHolder.html(
      "Have areas " + Object.keys(areas).join(', ') + "&hellip;"
    );    
    console.log(areas);
  }


  
  function make_bounds ( bounds ) {
      var sw = new google.maps.LatLng( bounds.south, bounds.west );
      var ne = new google.maps.LatLng( bounds.north, bounds.east );
      return new google.maps.LatLngBounds( sw, ne );
  }
  
  mzalendo_run_when_document_ready(
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
})();
