(function () {

  function initialize_map() {

    // Opera Mini
    if ( /Opera Mini/.test(navigator.userAgent) ) {
      $(".map-drilldown")
        .html('<div class="error">Your browser does not support Google Maps. Please <a href="/search/">search</a> for your constituency instead.</div>');
      return;
    }
    
    var map = createMap();
    addCrosshairs( map );
    trackMapMovements( map );   
    maintainMapCenterOnResize( map );
    addMessageControlToMap( map );
    addSearchByNameControlToMap( map );
    enableGeoLocation( map );
  }
  
  function createMap () {
    var map_element = document.getElementById("map-drilldown-canvas");
    if (!map_element) return false;

    var map_bounds = {
      north: window.mzalendo_settings.map_bounds.north,
      east:  window.mzalendo_settings.map_bounds.east,
      south: window.mzalendo_settings.map_bounds.south,
      west:  window.mzalendo_settings.map_bounds.west
    };

    var myOptions = {

      // Choose a map type that is clear
      mapTypeId: google.maps.MapTypeId.TERRAIN,

      // no point letting users zoom in too far for the purposes of finding a
      // constituency - adds server load and is not helpful to them.
      maxZoom: 12,
      
      // Use default controls (ie show or hide depending on device) and then
      // switch off irrelevant ones.
      disableDefaultUI:   false,
      mapTypeControl:     true,
      scaleControl:       false,
      streetViewControl:  false,
      overviewMapControl: false
      
    };

    var map = new google.maps.Map(map_element, myOptions);

    // We want a single click/tap to position the map where it was tapped. Add
    // smarts to wait and be sure that we didn't just trigger on the start of a
    // double tap, used to zoom. Could instead handle the zoom on dblclick
    // ourselves, but that could get tricky...
    var clickTimeoutId = null;
    google.maps.event.addListener(
      map,
      'click',
      function (event) {
        clickTimeoutId = setTimeout(
          function () { map.panTo(event.latLng); },
          400 // max delay between two clicks
        );
      }
    ); 
    google.maps.event.addListener(
      map,
      'dblclick',
      function () {
        clearTimeout(clickTimeoutId);
      }
    ); 

    map.fitBounds( make_bounds( map_bounds ) );
    
    return map;
  }

  function enableGeoLocation ( map ) {
    if ( geo_position_js.init() ) {      
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
    }    
  }

  // Add crosshairs at the center - see merging of answers at 
  // http://stackoverflow.com/questions/4130237
  function addCrosshairs ( map ) {
    var crosshairs_path = window.mzalendo_settings.static_url + 'images/crosshairs.png?' + window.mzalendo_settings.static_generation_number 

    var crosshairsImage = new google.maps.MarkerImage(
       crosshairs_path,                 // marker image
       new google.maps.Size(63, 63),    // marker size
       new google.maps.Point(0,0),      // marker origin
       new google.maps.Point(32, 32)    // marker anchor point
    );
    
    var crosshairsShape = {
      coords: [32,32,32,32],           // 1px
      type: 'rect'                     // rectangle
    };
    
    var crosshairsMarker = new google.maps.Marker({
      map: map,
      icon: crosshairsImage,
      position: map.getCenter(),
      clickable: false,
      draggable: false,
      visible:   true
    });
    
    crosshairsMarker.bindTo('position', map, 'center');
    
  }
  
  function reducePrecision (val) {
    var precision = 100;
    return Math.round(val * precision ) / precision;
  };

  function trackMapMovements( map ) {
    google.maps.event.addListener(
      map,
      'center_changed',
      function () { updateLocation( map.getCenter() ); }
    ); 
  }
  

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
    fetchAreasDebounceTimeout = setTimeout(
      function () {
        // TODO - catch errors here and display them (ignoring aborts)
        messageHolderHTML("Fetching area from server&hellip;");
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
      area_descriptions += '<a href="/place/mapit_area/' + area_id + '">' + area.name + ' (' + area.type_name + ')</a>';
    });

    messageHolderHTML(
      area_descriptions || default_message
    );    
  }
  

  function addMessageControlToMap (map) {
    var control = $('#map-drilldown-message').get(0);
    control.index = 1;
    map
      .controls[google.maps.ControlPosition.TOP_CENTER]
      .push(control);
    $(control).show();
  }

  function addSearchByNameControlToMap (map) {
    var control = $('#search-by-name-button').get(0);
    control.index = 1;
    map
      .controls[google.maps.ControlPosition.RIGHT_BOTTOM]
      .push(control);
    $(control).show();
  }

  function messageHolderHTML (html) {
    $('#map-drilldown-message').html( html );        
  }


  
  function make_bounds ( bounds ) {
      var sw = new google.maps.LatLng( bounds.south, bounds.west );
      var ne = new google.maps.LatLng( bounds.north, bounds.east );
      return new google.maps.LatLngBounds( sw, ne );
  }


  function centerMapInWindow (map, loc) {
    
    // Make the map the same height as the window, and then scroll to the top
    // of it to fill the window
    var $canvas = $('#map-drilldown-canvas');
    $canvas.height( $(window).height() );
    google.maps.event.trigger(map, 'resize');
    window.scrollTo( 0, $canvas.offset().top );

    if ( loc ) {
      map.setCenter( loc );
    }
  }
  

  function maintainMapCenterOnResize (map) {

    centerMapInWindow(map);
    
    // Maintain the centre of the map in the same place when the window is
    // resized (includes changing screen orientation).
    // Adapted from http://stackoverflow.com/q/8792676/5349
    var currentMapCenter = null;

    // When the map is not moving store the current location. Use a timeout so rapid
    // changes do not get stored, which is what happens when the resize and
    // orientationchange events fire in succession on a mobile.
    google.maps.event.addListener(
      map,
      'idle',
      _.debounce(
        function () {
          var center = map.getCenter();
          currentMapCenter = new google.maps.LatLng( center.lat(), center.lng() );        
        },
        400
      )
    );

    // Handle events - debounce these as well
    var eventHandler = _.debounce(
      function () {
        centerMapInWindow( map, currentMapCenter );
      },
      200
    );
    google.maps.event.addDomListener( window, 'resize',            eventHandler);    
    google.maps.event.addDomListener( window, 'orientationchange', eventHandler);    
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
