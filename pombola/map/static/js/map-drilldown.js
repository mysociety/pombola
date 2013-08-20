(function () {

  var MzMap = function () {

    this.markers = [];

    this.init = function() {
      // Opera Mini
      if ( /Opera Mini/.test(navigator.userAgent) ) {
        $(".map-drilldown")
          .html('<div class="error">' + this.toMessage("browser not supported") + '</div>');
        return;
      }

      this.createMap();

      this.addMessageControlToMap();
      this.addCrosshairs();

      this.trackMapMovements();
      this.maintainMapCenterOnResize();

      this.enableGeoLocation();

      this.enableGeocoder();
    };

    this.createMap = function () {
      var map_element = document.getElementById("map-drilldown-canvas");
      if (!map_element) return false;

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

      map.fitBounds( this.make_bounds() );

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
      var crosshairs_path = window.pombola_settings.static_url + 'images/crosshairs.png?' + window.pombola_settings.static_generation_number

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


    this.toMessage = function ( key ) {
      return mapDrilldownSettings.i18n[key] || key;
    }


    this.messageHolderHTMLInstruction = function (html) {
      $('#map-drilldown-message div.instruction').html( this.toMessage(html) );
    };

    this.messageHolderHTMLLocation = function (html) {
      $('#map-drilldown-message div.location').html( this.toMessage(html) );
    };



    this.make_bounds = function () {

        var bounds = {
          north: window.pombola_settings.map_bounds.north,
          east:  window.pombola_settings.map_bounds.east,
          south: window.pombola_settings.map_bounds.south,
          west:  window.pombola_settings.map_bounds.west
        };

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

    this.enableGeocoder = function () {
      var self = this;
      var geocoder = new google.maps.Geocoder();

      var $search_form  = $('#map-drilldown-message form.search');
      var $search_input = $search_form.find('input[type="search"]');

      $search_form.submit(
        function (event) {

          // There is nowhere else for the form to submit to
          event.preventDefault();

          // Tell the user that we are searching, it's a remote call so may take
          // a while to come back
          self.messageHolderHTMLLocation("geocoder searching");

          // construct the search arguments, including country bounds.
          var geocoder_args = {
            address: $search_input.attr("value"),
            bounds: self.make_bounds()
          };

          // start the geocoding request
          geocoder.geocode(
            geocoder_args,
            function (results, status) {

              // filter out results that are not in the area we're interested in (we hint to
              // google where to search, but they sometimes ignore the hint).
              var desired_bounds = self.make_bounds();
              results = _.filter(results, function (result) {
                return desired_bounds.contains(result.geometry.location);
              });

              // found no matches (or no matches that are within our bounds)
              if (status == google.maps.GeocoderStatus.ZERO_RESULTS || (status == google.maps.GeocoderStatus.OK && results.length == 0) ) {
                self.messageHolderHTMLLocation( "zero geocoder results");
              }

              // found some matches
              else if (status == google.maps.GeocoderStatus.OK) {

                var map = self.map;

                // handler for marker clicks - go to latlng view
                var marker_click_handler = function(event) {
                  var loc = event.latLng;
                  var path = "/place/latlon/" + loc.lat()  + "," + loc.lng() + "/";
                  document.location = path;
                };

                // Remove all the existing markers from the map
                _.each(self.markers, function (marker) {
                  marker.setMap(null);
                });
                self.markers = [];

                // for each result...
                _.each( results, function (result) {

                  // ...create a marker and add it to the map
                  var marker = new google.maps.Marker({
                    map: map,
                    position: result.geometry.location,
                    title: result.formatted_address,
                  });

                  // ...set the click handler
                  google.maps.event.addListener(marker, "click", marker_click_handler);

                  // ...add to marker array for later reference
                  self.markers.push(marker);
                });

                // Once all the pins are on we want to make sure they are
                // visible on the map. Use a bounds to cover them all and then
                // fit the map to it.
                var marker_bounds = new google.maps.LatLngBounds();
                _.each( self.markers, function (marker) {
                  marker_bounds.extend(marker.getPosition());
                });
                map.fitBounds(marker_bounds);

                // All done, display a message to the user
                self.messageHolderHTMLLocation( "geocoder results displayed");
              }

              // other (most likely an error)
              else {
                self.messageHolderHTMLLocation( "geocoder error");
              }

            }
          );
        }
      );

    };

  };



  pombola_run_when_document_ready(
      function () {
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
      }
  );


})();
