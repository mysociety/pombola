(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/analytics.js','ga');

ga('create', pombola_settings.google_analytics_account);
ga('send', 'pageview');

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
