(function () {

  var MzMap = function () {

    this.init = function() {
      // Opera Mini
      if ( /Opera Mini/.test(navigator.userAgent) ) {
        $(".map-drilldown")
          .html('<div class="error">Your browser does not support Google Maps. Please <a href="/search/">search</a> for your constituency instead.</div>');
        return;
      }

      this.createMap();

      this.addMessageControlToMap();
      this.addCrosshairs();

      this.trackMapMovements();
      this.maintainMapCenterOnResize();

      this.enableGeoLocation();
    };

    this.createMap = function () {
      var map_element = document.getElementById("map-drilldown-canvas");
      if (!map_element) return false;

      var map_bounds = {
        north: window.pombola_settings.map_bounds.north,
        east:  window.pombola_settings.map_bounds.east,
        south: window.pombola_settings.map_bounds.south,
        west:  window.pombola_settings.map_bounds.west
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

      var map = this.map = new google.maps.Map(map_element, myOptions);

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

      map.fitBounds( this.make_bounds( map_bounds ) );

      return map;
    };

    this.enableGeoLocation = function () {
      var self = this;
      var map = this.map;
      if ( geo_position_js.init() ) {
        self.messageHolderHTMLInstruction('geolocating');
        geo_position_js.getCurrentPosition(
          function (data) { // success
            var coords = new google.maps.LatLng( data.coords.latitude, data.coords.longitude );
            map.setCenter( coords );
            map.setZoom( 10 ); // feels about right for locating a big area
            self.messageHolderHTMLInstruction('location found');
            setTimeout(function() {
              self.messageHolderHTMLInstruction('drag to find');
            }, 2000);
          },
          function () { // failure or error
            self.messageHolderHTMLInstruction('could not geolocate');
            setTimeout(function() {
              self.messageHolderHTMLInstruction('drag to find');
            }, 2000);
          }
        );
      }
    };

    // Add crosshairs at the center - see merging of answers at
    // http://stackoverflow.com/questions/4130237
    this.addCrosshairs = function () {
      var map = this.map;

      var crosshairsImage = new google.maps.MarkerImage(
         window.pombola_settings.crosshairs_image, // marker image
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

    };

    this.reducePrecision = function (val) {
      var precision = 100;
      return Math.round(val * precision ) / precision;
    };

    this.trackMapMovements = function () {
      var self = this;
      var map = this.map;
      google.maps.event.addListener(
        map,
        'center_changed',
        function () { self.updateLocation( map.getCenter() ); }
      );
    };


    this.updateLocation = function (latlng) {

        var lat = this.reducePrecision( latlng.lat() );
        var lng = this.reducePrecision( latlng.lng() );

        this.fetchAreas( lat, lng );
    };


    // Get the areas hash from the server, or the local cache. Debounce as well
    // so that we don't issue too many requests during map movements.

    this.fetchAreasCurrentRequest  = null;
    this.fetchAreasDebounceTimeout = null;
    this.fetchAreasCurrentURL      = null;
    this.fetchAreasCache           = {};

    this.fetchAreas = function ( lat, lng ) {
      var self = this;

      var mapitPointURL = '/mapit/point/4326/' + lng + ',' + lat;

      // Add the con
      if (mapDrilldownSettings.mapitAreaType) {
        mapitPointURL += "?type=" + mapDrilldownSettings.mapitAreaType;
      }

      // console.log(lat, lng, mapitPointURL);

      // Check that we are not at the current location already
      if (mapitPointURL == self.fetchAreasCurrentURL) {
        return;
      }
      self.fetchAreasCurrentURL = mapitPointURL;

      // clear current request and timeout
      clearTimeout(self.fetchAreasDebounceTimeout);
      if (self.fetchAreasCurrentRequest) {
        self.fetchAreasCurrentRequest.abort();
      }

      // Check to see if we have this result in cache already
      if (self.fetchAreasCache[mapitPointURL]) {
        self.displayAreas( self.fetchAreasCache[mapitPointURL] );
        return;
      }

      // Not in cache - fetch from server
      self.fetchAreasDebounceTimeout = setTimeout(
        function () {
          // TODO - catch errors here and display them (ignoring aborts)
          self.messageHolderHTMLLocation("Fetching area from server&hellip;");
          self.fetchAreasCurrentRequest = $.getJSON( mapitPointURL, function (data) {
            self.fetchAreasCache[mapitPointURL] = data;
            self.displayAreas(data);
          } );
        },
        1000
      );
    };


    this.displayAreas = function (data) {

      var areas = _.omit( data, ['debug_db_queries'] );
      var default_message   = 'area not found';
      var area_descriptions = '';

      _.each( areas, function (area, area_id ) {
        // console.log(area);
        if (area_descriptions) { area_descriptions += ', '; }
        area_descriptions += '<a href="/place/mapit_area/' + area_id + '">' + area.name + ' (' + area.type_name + ')</a>';
      });

      this.messageHolderHTMLLocation(
        area_descriptions || default_message
      );
    };


    this.addMessageControlToMap = function () {
      var map = this.map;
      var control = $('#map-drilldown-message').get(0);
      control.index = 1;
      map
        .controls[google.maps.ControlPosition.TOP_CENTER]
        .push(control);
      $(control).show();
    };


    this.messages = {
      "drag to find": 'Drag map to your location or <a href="/search">search by name</a>.',
      'geolocating':  "Trying to find your current location&hellip;",
      'could not geolocate': "There was a problem finding your current location.",
      'location found':      "Map has been centred on your current location.",
      'area not found':      "No matching areas were found.",
    };

    this.toMessage = function ( key ) {
      return this.messages[key] || key;
    }


    this.messageHolderHTMLInstruction = function (html) {
      $('#map-drilldown-message div.instruction').html( this.toMessage(html) );
    };

    this.messageHolderHTMLLocation = function (html) {
      $('#map-drilldown-message div.location').html( this.toMessage(html) );
    };



    this.make_bounds = function ( bounds ) {
        var sw = new google.maps.LatLng( bounds.south, bounds.west );
        var ne = new google.maps.LatLng( bounds.north, bounds.east );
        return new google.maps.LatLngBounds( sw, ne );
    };


    this.centerMapInWindow = function (loc) {
      var map = this.map;

      // Make the map the same height as the window, and then scroll to the top
      // of it to fill the window
      var $canvas = $('#map-drilldown-canvas');
      $canvas.height( $(window).height() );
      google.maps.event.trigger(map, 'resize');
      window.scrollTo( 0, $canvas.offset().top );

      if ( loc ) {
        map.setCenter( loc );
      }
    };


    this.maintainMapCenterOnResize = function () {
      var self = this;
      var map = this.map;

      this.centerMapInWindow();

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
          self.centerMapInWindow( currentMapCenter );
        },
        200
      );
      google.maps.event.addDomListener( window, 'resize',            eventHandler);
      google.maps.event.addDomListener( window, 'orientationchange', eventHandler);
    };

  };



  google.load(
    'maps', '3',
    {
        callback: function () {
          var myMzMap = new MzMap();
          myMzMap.init();
        },
        other_params:'sensor=true'
    }
  );


})();
