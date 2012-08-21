function addNavigJs(io)
{
	$(".textinput").attr("autocomplete", "off");
	//NOTIFICATIONS
/*	var sock = io.connect('http://localhost:3000/streamposts');
	sock.on('connect', function(){});
	sock.on('notification', function(from, msg){
		var num = $("#not-btn").text();
		$("#not-btn").text((num - '0') + 1);
		$("#no-courses").hide();
		var obj = JSON.parse(msg);
		if(obj.type == "STREAM")
			$(".not-bubble").prepend('<div class="notification"><table><tr><td><a href="/courses/' + obj.course_id + '/main#' + obj.reference + '"><div class="img"><img style="width: 50px" src="/images/post/' + obj.img_id + '" /></div></a></td><td><a href="/courses/' + obj.course_id + '/main#' + obj.reference + '"><div class="notif-content"> ' + obj.first_name + ' ' + obj.last_name + ' posted in <span class="notif-course">' + obj.course_name + '</span></div></a></td></tr></table></div>');
		$("#not-btn").addClass("green-btn");
	});*/

	$(".notification").mouseover(
		function(){
			$(this).find('.notif-content').addClass("notif-content-hover");
			$(this).find('.notif-event-date').addClass("notif-event-date-hover");
		}
	);
	$(".notification").mouseout(
		function(){
			$(this).find('.notif-content').removeClass("notif-content-hover");
			$(this).find('.notif-event-date').removeClass("notif-event-date-hover");
		}
	);


	//SEARCH PROPERTIES
	$("#search-btn").click(
		function(e){
			if($("#search-txtbox").val().trim() == ""){
				$("#search-txtbox").val("");
				e.preventDefault();
				$("#search-txtbox").focus();
			}
		}
	);


	//MODAL WINDOW PROPERTIES
	$(".modal-window").dialog({autoOpen: false, minWidth: 100, minHeight: 100, modal: true, resizable: false, draggable: false});

	/*$(document).keyup(function(e){
		if(e.keyCode == 27)
			$(".modal-window").hide();
	});*/
	$(".cancel").click(
		function(e){
			e.preventDefault();
			$(".modal-window").dialog("close");
		}
	);

	/*$(document).bind("click", function(e){
		var $clicked = $(e.target);
		if(!$clicked.parents().hasClass("modal-window") && !$clicked.hasClass("modal-window") && $(".modal-window").css("display") != "hidden")
			$(".modal-window").hide();
	});*/

	//DROP DOWN MENUS
	$("#course-list").click(
		function(e){
			e.preventDefault();
			$(".bubble").toggle();
			if($(".bubble").css("display") == "none")
				$(".dropdown a").removeClass("selected");
			else
				$(".dropdown a").addClass("selected");
		}
	);
	$("#not-btn").click(
		function(e){
			e.preventDefault();
			$(this).removeClass("green-btn");
			$(this).text(0);
			$(".not-bubble").toggle();
			var n = $(".notification");
			var idlist = [];
			for(var i = 0; i < n.length; i++)
				idlist.push(toNum(n[i].id));
			$.post("/notif_complete", {ids: idlist}, function(ret){});
		}
	);
	$("#actions").click(
		function(e){
			e.preventDefault();
			$(".action-bubble").toggle();
		}
	);
	$("#me").click(
		function(e){
			e.preventDefault()
			$(".me-bubble").toggle();
		}
	);
	/*
	$(".button").click(
		function(e){
			if(!$(this).siblings(".textinput").val() || $(this).siblings(".textinput").val() == "" || $(this).siblings(".textinput").val().trim() == ""){
				e.preventDefault();
				$(this).siblings(".textinput").val("");
				$(this).siblings(".textinput").focus();
			}
		}
	);
	*/
}
function prettyDate(stamp){
	var date = new Date(stamp * 1000)
	var m = "AM";
	var hours = date.getHours();
	if(hours > 12){
		m = "PM";
		hours = hours % 12;
	}
	var minutes = date.getMinutes();
	var formattedTime = hours + ':' + minutes + " " + m + "&nbsp&nbsp" + date.toLocaleDateString();
	return formattedTime;
}

function toNum(str){
	var num = 0;
	for(var i = 0; i < str.length; i++)
		num += 10 * num + (str.charAt(i) - '0');
	return num;
}
