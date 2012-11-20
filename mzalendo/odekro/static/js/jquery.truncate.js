(function($) {
	
	$.fn.truncate = function(options) {   
		var defaults = {
		charLength: 400, //chacracters to show up until
		minTrail: 20,
		perOT: false,
		moreTitle: "more",
		lessTitle: "less",
		ellipsisText: "...",
		speed: 1000,
		fx:'jswing'   
	};
  
  var options = $.extend(defaults, options);
    
  return $(this).each(function() {
	obj = $(this);
	var body = obj.html();
	var new_height,orig_height, orig_text, new_text;
   
	orig_text = obj.html();


	//If percentage is set
	if (options.perOT){
	   options.charLength = body.length * (options.charLength / 100);
	}
   
   
	new_text = orig_text.substr(0,options.charLength - 1);
	orig_height = obj.height();

	if(body.length > options.charLength + options.minTrail) 
	{
		var splitLocation = body.indexOf(' ', options.charLength);
		if(splitLocation != -1) 
		{
		
			 var html;
			 var splitLocation = body.indexOf(' ', options.charLength);
			 var str1 = body.substring(0, splitLocation);
			 var str2 = body.substring(splitLocation, body.length - 1);
			 
			 
			new_height = obj.html(new_text + options.ellipsisText).height();
			obj.css("overflow", "hidden"); 
			obj.css("height",new_height);

			 // insert more link
			 obj.after(
			  '<div class="clearboth">' +
			   '<a href=".'+ obj.attr('class') +'" class="truncate_more_link">' +  options.moreTitle + '</a>' + 
			  '</div>'
			 );

			 var moreLink = $("."+obj.attr('class') + 'Container .truncate_more_link');
			 var moreContent = $("."+obj.attr('class') + 'Container .truncate_more');
			 var ellipsis = $("."+obj.attr('class') + 'Container .truncate_ellipsis');
			 
			 //More
			 moreLink.click(function() {
			 
			 eleDiv = $(this).attr('href');
			 
			if(moreLink.text() == options.moreTitle) {

				moreLink.text(options.lessTitle);
				ellipsis.css("display", "none");


				$(eleDiv).animate({height: orig_height}, {duration: options.speed,easing:options.fx});


				$(eleDiv).html(orig_text);

			} else {
				//Less
				moreLink.text(options.moreTitle);
				ellipsis.css("display", "inline");

				$(eleDiv).animate({height: new_height}, {duration: options.speed,easing:options.fx});
				setTimeout(function(){$(eleDiv).html(new_text + options.ellipsisText)},1000);

			   
			}
			 return false;
			});
		}
		
		
	} // end if
   
  });
};
})(jQuery);