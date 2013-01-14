(function () {

  function initialize_map() {

    var map_element = document.getElementById("map-drilldown-canvas");
    if (!map_element) return false;

    var map_bounds = {
      north: window.mzalendo_settings.map_bounds.north,
      east:  window.mzalendo_settings.map_bounds.east,
      south: window.mzalendo_settings.map_bounds.south,
      west:  window.mzalendo_settings.map_bounds.west
    };

    var map_has_been_located = false;

    var myOptions = {

      // Choose a map type that is clear
      mapTypeId: google.maps.MapTypeId.TERRAIN,

      // no point letting users zoom in too far for the purposes of finding a
      // constituency - adds server load and is not helpful to them.
      maxZoom: 10,
      
      // Use limited controls
      disableDefaultUI:   true,
      panControl:         true,
      zoomControl:        true,
      zoomControlOptions: {
        style: google.maps.ZoomControlStyle.SMALL
      },
      mapTypeControl:     false,
      scaleControl:       false,
      streetViewControl:  false,
      overviewMapControl: false
      
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
    
    maintainMapCenterOnResize( map );
    
    addMessageControlToMap( map );

    var $geoLocateMeButton = $('#geo-locate-me-button').find('a');
    if ( geo_position_js.init() ) {      

      $geoLocateMeButton
        .click( function (event) {
          event.preventDefault();
          
          messageHolderHTML('Trying to find your current location&hellip;');
          geo_position_js.getCurrentPosition(
            function (data) { // success
              var coords = new google.maps.LatLng( data.coords.latitude, data.coords.longitude );
              map.setCenter( coords );
              map.setZoom( 10 ); // feels about right for locating a big area
            },
            function () { // failure or error
              messageHolderHTML('There was a problem finding your current location');
            }
          );
        
        });
        addGeoLocateControlToMap( map );
    } else {
      $geoLocateMeButton.hide();      
    }

    
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

    // FIXME - change to CON after #495 closed.
    var mapitPointURL = '/mapit/point/4326/' + lng + ',' + lat + '?type=con';
    // console.log(lat, lng, mapitPointURL);

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
    messageHolderHTML("Fetching area from server&hellip;");
    fetchAreasDebounceTimeout = setTimeout(
      function () {
        // TODO - catch errors here and display them (ignoring aborts)
        fetchAreasCurrentRequest = $.getJSON( mapitPointURL, function (data) {
          fetchAreasCache[mapitPointURL] = data;
          displayAreas(data);
        } );         
      },
      1000
    );  
  }
  
  function displayAreas (data) {

    var areas = _.omit( data, ['debug_db_queries'] );
    var default_message   = 'No matching areas were found';
    var area_descriptions = '';

    _.each( areas, function (area, area_id ) {
      // console.log(area);
      if (area_descriptions) { area_descriptions += ', '; } 
      area_descriptions += '<a href="/place/mapit_area/' + area_id + '">' + area.name + '</a> (' + area.type_name + ')';
    });

    messageHolderHTML(
      area_descriptions || default_message
    );    
  }
  

  function addMessageControlToMap (map) {
    map
      .controls[google.maps.ControlPosition.TOP_CENTER]
      .push($('#map-drilldown-message').get(0));
  }

  function addGeoLocateControlToMap (map) {
    map
      .controls[google.maps.ControlPosition.TOP_RIGHT]
      .push($('#geo-locate-me-button').get(0));
  }


  function messageHolderHTML (html) {
    $('#map-drilldown-message').html( html );        
  }


  
  function make_bounds ( bounds ) {
      var sw = new google.maps.LatLng( bounds.south, bounds.west );
      var ne = new google.maps.LatLng( bounds.north, bounds.east );
      return new google.maps.LatLngBounds( sw, ne );
  }

  function maintainMapCenterOnResize (map) {
    // Maintain the centre of the map in the same place when the window is
    // resized (includes changing screen orientation).
    // Adapted from http://stackoverflow.com/q/8792676/5349
    var currentMapCenter = null;
    google.maps.event.addListener( map, 'idle', function () {
        currentMapCenter = map.getCenter();
    });
    google.maps.event.addDomListener( window, 'resize', function () {
      map.setCenter(currentMapCenter);
    });    
    google.maps.event.addDomListener( window, 'orientationchange', function () {
      map.setCenter(currentMapCenter);
    });    
  }
  
  mzalendo_run_when_document_ready(
      function () {
          google.load(
              'maps', '3',
              {
                  callback: initialize_map,
                  other_params:'sensor=true'
              }
          );
      }
  );
})();
