// add in some tracking to detect when users print pages. Will be used to judge
// how often this happens.


(function() {
  // based on code from http://stackoverflow.com/a/11060206/5349  

  // track the print request - with debounce for chrome.
  var haveTracked = false;
  var beforePrint = function() {
    if (haveTracked)
      return;
    haveTracked = true;
    var args = ['_trackEvent', 'Sharing', 'Print', document.location.pathname];
    // console.log(args)
    _gaq.push(args);
  };

  // respond to print events
  if (window.matchMedia) {
    var mediaQueryList = window.matchMedia('print');
    mediaQueryList.addListener(function(mql) {
      if (mql.matches) {
        beforePrint();
      }
    });
  }
  window.onbeforeprint = beforePrint;

}());
