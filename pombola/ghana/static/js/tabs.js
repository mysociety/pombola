/***************************/
//@Author: Adrian "yEnS" Mato Gondelle & Ivan Guardado Castro
//@website: www.yensdesign.com
//@email: yensamg@gmail.com
//@license: Feel free to use it, but keep this credits please!					
/***************************/
$(document).ready(function(){
	$(".menu > li").click(function(e){
		switch(e.target.id){
			case "comments":
				//change status & style menu
				$("#comments").addClass("active");
				$("#overview").removeClass("active");
				$("#experience").removeClass("active");
				$("#appearances").removeClass("active");
				//display selected division, hide others
				$("div.comments").fadeIn();
				$("div.overview").css("display", "none");
				$("div.experience").css("display", "none");
				$("div.appearances").css("display", "none");
			break;
			case "overview":
				//change status & style menu
				$("#comments").removeClass("active");
				$("#overview").addClass("active");
				$("#experience").removeClass("active");
				$("#appearances").removeClass("active");
				//display selected division, hide others
				$("div.comments").css("display", "none");
				$("div.overview").fadeIn();
				$("div.experience").css("display", "none");
				$("div.appearances").css("display", "none");
			break;
			case "experience":
				//change status & style menu
				$("#comments").removeClass("active");
				$("#overview").removeClass("active");
				$("#experience").addClass("active");
				$("#appearances").removeClass("active");
				//display selected division, hide others
				$("div.comments").css("display", "none");
				$("div.overview").css("display", "none");
				$("div.experience").fadeIn();
				$("div.appearances").css("display", "none");
			break;
			case "appearances":
				//change status & style menu
				$("#comments").removeClass("active");
				$("#overview").removeClass("active");
				$("#experience").removeClass("active");
				$("#appearances").addClass("active");
				//display selected division, hide others
				$("div.comments").css("display", "none");
				$("div.overview").css("display", "none");
				$("div.experience").css("display", "none");
				$("div.appearances").fadeIn();
			break;
		}
		//alert(e.target.id);
		return false;
	});
});