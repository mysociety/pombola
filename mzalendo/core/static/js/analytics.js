 // mathiasbynens.be/notes/async-analytics-snippet
var _gaq = [["_setAccount", mzalendo_settings.google_analytics_account], ["_trackPageview"]];
(function(d, t) {
  var g = d.createElement(t), s = d.getElementsByTagName(t)[0];
  g.async = 1;
  g.src = ("https:" == location.protocol ? "//ssl" : "//www") + ".google-analytics.com/ga.js";
  s.parentNode.insertBefore(g, s)
}(document, "script"));
