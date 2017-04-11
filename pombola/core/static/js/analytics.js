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

  window.analytics = {
    trackEvents: function(listOfEvents){
      // Takes a list of arguments suitable for trackEvent.
      // Returns a jQuery Deferred object.
      // The deferred object is resolved when
      // all of the trackEvent calls are resolved.
      var dfd = $.Deferred();
      var deferreds = [];
      var _this = this;
      $.each(listOfEvents, function(i, params){
          deferreds.push(_this.trackEvent(params));
      });
      $.when.apply($, deferreds).done(function(){
          dfd.resolve();
      });
      return dfd.promise();
    },

    trackEvent: function(params){
      // Takes an object of event parameters, eg:
      // { eventCategory: 'foo', eventAction: 'bar' }
      // Returns a jQuery Deferred object.
      // The deferred object is resolved when the GA call
      // completes or fails to respond within 2 seconds.
      var dfd = $.Deferred();

      if(typeof ga === 'undefined' || !ga.loaded){
        // GA has not loaded (blocked by adblock?)
        return dfd.resolve();
      }

      var defaults = {
        hitType: 'event',
        eventLabel: document.title,
        hitCallback: function(){
          dfd.resolve();
        }
      }

      ga('send', $.extend(defaults, params));

      // Wait a maximum of 2 seconds for GA response.
      setTimeout(function(){
        dfd.resolve();
      }, 2000);

      return dfd.promise();
    }
  };

}());
