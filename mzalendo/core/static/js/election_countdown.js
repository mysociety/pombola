$(function() {
  
  // Election is on 2013/3/4 according to http://en.wikipedia.org/wiki/2013_Kenyan_General_Election
  var $electionCountdown = $("#election_countdown");

  var args         = $electionCountdown.data();
  var electionDate = new Date( args.until );

  var $day    = $electionCountdown.find('.countdown_day    .countdown_amount'),
      $hour   = $electionCountdown.find('.countdown_hour   .countdown_amount'),
      $minute = $electionCountdown.find('.countdown_minute .countdown_amount'),
      $second = $electionCountdown.find('.countdown_second .countdown_amount');

  var tidyDigits = function (digit) {
    var string = digit + '';
    if (string.length == 1 ) {
      string = '0' + string;
    }
    return string;
  };

  var updateCountdown = function () {
    var remaining = Math.floor((electionDate - Date.now()) / 1000);

    // If election has passed display zeros.
    if ( remaining < 0 ) remaining = 0;

    var days    = Math.floor(remaining / 86400);
    remaining   -= days * 86400;
    var hours   = Math.floor( remaining / 3600 );
    remaining   -= hours * 3600;
    var minutes = Math.floor( remaining / 60 );
    remaining   -= minutes * 60;
    var seconds = remaining;
    
    // console.log({ days: days, hours: hours, minutes: minutes, seconds: seconds });

    $day.html(    tidyDigits(days   ) );
    $hour.html(   tidyDigits(hours  ) );
    $minute.html( tidyDigits(minutes) );
    $second.html( tidyDigits(seconds) );

  }

  // Execute every second
  updateCountdown();
  setInterval( updateCountdown, 1000 );
  
});
