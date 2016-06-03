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

      this.messageHolderHTMLLocation("ready to search");
    };


    this.createMap = function () {
      var self = this;
      var map_element = document.getElementById("map-drilldown-canvas");
      if (!map_element) return false;

      var myOptions = {

        // Choose a map type that is clear
        mapTypeId: google.maps.MapTypeId.TERRAIN,

        // use the pointer, to indicate that a click is expected (can still
        // drag and dbl-click to zoom though, so this is not ideal)
        draggableCursor: "pointer",

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
            function () { self.clickEventHandler(event) },
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

      var $canvas = $('#map-drilldown-canvas');

      // Slightly annoying that what is a small window (less than 640 pixels wide)
      // is being set independently of the css.
      var window_is_large = $(window).width() >= 640;
      var canvas_offset = $canvas.offset().top;

      $canvas.height( $(window).height() - (window_is_large ? canvas_offset : 0) );

      window.scrollTo(0, window_is_large ? 0 : canvas_offset);

      google.maps.event.trigger(map, 'resize');

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


    // redirect to the location of the click
    this.clickEventHandler = function(event) {
      var self = this;
      var precision = 3; // suitable for the max zoom we allow
      var path = "/place/latlon/" + event.latLng.toUrlValue(precision) + "/";

      var xhr = $.ajax({
        url: path
      });

      xhr.success(function() {
        document.location = path;
      }).error(function() {
        self.messageHolderHTMLLocation("outside map bounds");
        setTimeout(function() {
          self.messageHolderHTMLLocation("ready to search");
        }, 3000);
      });
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
                  google.maps.event.addListener(marker, "click", self.clickEventHandler);

                  // ...add to marker array for later reference
                  self.markers.push(marker);
                });

                // Once all the pins are on we want to make sure they are
                // visible on the map. Use a bounds to cover them all and then
                // fit the map to it. Use the viewport to create the bounds.
                var viewport_bounds = new google.maps.LatLngBounds();
                _.each( results, function (result) {
                  viewport_bounds.union(result.geometry.viewport);
                });
                map.fitBounds(viewport_bounds);

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
