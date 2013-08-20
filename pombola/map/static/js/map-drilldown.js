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
      this.maintainMapCenterOnResize();
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

      map.fitBounds( this.make_bounds() );

      return map;
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
