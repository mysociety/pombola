$(function() {
  var updateRepLocatorTabZoom = function(tabID) {
    if (map) {
        remove_kml_layers();
        remove_markers();
        if (tabID == 'councillors') {
            add_kml_urls(ward_kml_urls);
        } else if (tabID == 'mps') {
            add_markers(constituency_offices_marker_data);
        }
    }
  }
  map_loaded_callbacks.push(function(map) {
    var tabIndex, tabID;
    // Find the tab which is active, and set the zoom level for it:
    tabIndex = $(".rep-locator-container").tabs('option', 'active');
    tabID = $(".tabs .tab-content").eq(tabIndex).attr('id');
    updateRepLocatorTabZoom(tabID);
    // Now add event listeners to detect changes of tab and rezoom
    // the map:
    $(".rep-locator-container").on("tabsactivate", function(event, ui) {
      updateRepLocatorTabZoom(ui.newPanel[0].id);
    });
  });
  $(".tabs").tabs();
  $(".tabs").on("tabsactivate", function(event, ui) {
    history.pushState(null, null, '#' + ui.newPanel[0].id);
  });
});
