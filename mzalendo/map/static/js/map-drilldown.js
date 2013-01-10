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
