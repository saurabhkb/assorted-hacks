$("document").ready(
	function(){
//		$(".textinput").attr("autocomplete", "off");
		$(document).bind("click", function(e){
			var $clicked = $(e.target);
			if(!$clicked.parents().hasClass("dropdown") && !$clicked.parents().hasClass("bubble"))
			{
				$(".bubble").hide();
				$(".dropdown a").removeClass("selected");
				$(".bubble input[type='text']").val("");
				$(".bubble input[type='password']").val("");
			}
		});
		$(".dropdown").click(
			function(e)
			{
				e.preventDefault();
				$(".bubble").toggle();
				if($(".bubble").css("display") == "none")
					$(".dropdown a").removeClass("selected");
				else
					$(".dropdown a").addClass("selected");
			}
		);

	}
);
