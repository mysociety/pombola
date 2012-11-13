$(function() {
  
  // Election is on 2013/3/4 according to http://en.wikipedia.org/wiki/2013_Kenyan_General_Election
  // Would be nice to put in the time that the polls open too.
  var election_countdown = $("#election_countdown");

  var args = election_countdown.data();
  args.until = new Date( args.until );
  election_countdown.countdown( args );
});