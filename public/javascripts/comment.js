function comment(){
	var socket = io.connect("http://localhost:3000/assignment_comments");
	$(".comments a").click(
			function(e){
				e.preventDefault();
				$(".load-comments").show();
				$("#comments-window").dialog("open");
				$("#comments-window").dialog("option", "width", 600);
				$("#comments-window").dialog("option", "title", "Comment");
				$("#comments-window").dialog("option", "height", 500);
				$("#comments-window").dialog({close: function(e, ui){$("#comment-list").html("");}});
				var uid = $(this).parents("td").children(".comment_user_id").val();
				$("#comments-window #user_id").val(uid);
				$.post("/courses/#{loc.course_id}/assignments/#{assg.id}/comments/", {user_id: uid}, function(json){
					$(".load-comments").hide();
					var com = JSON.parse(json);
					for(var i = 0; i < com.length; i++)
						$("#comment-list").append("<div class='comment-unit'><table><tr><td><div class='comment-img'><a href='/user/" + com[i].user_id + "/'><img src='/images/user/" + com[i].img_id + "', title='" + com[i].first_name + " " + com[i].last_name + "'/></a></div></td><td><div class='comment-text'>" + com[i].comment + "</div></td></tr></table></div>");
				});
				return false;
			}
		);
		$("#add-comment-btn").click(
			function(e){
				e.preventDefault();
				var cmment = $("#comments-window #comment-box").val().trim();
				var target = $(this).siblings("#user_id").val();
				if(cmment){
					$("#comment-list").append("<div class='comment-unit'><table><tr><td><div class='comment-img'><a href='/user/#{me.user_id}/'><img src='/images/user/#{me.img_id}', title='#{me.first_name} #{me.last_name}'/></a></div></td><td><div class='comment-text'>" + cmment + "</div></td></tr></table></div>");
					socket.emit('assignment comment', JSON.stringify({target_id: target, comment: cmment, a_id: aid}));
				}
				$("#comment-box").val("");
				$("#comment-box").focus();
				return false;
			}
		);
}
