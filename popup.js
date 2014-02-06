$("document").ready(
	function() {
		get_ranks();
	}
);
/*function hyperlink_enable() {
	$("body").on(
		"click",
		"a.item",
		function() {
			chrome.tabs.create({url: $(this).attr('href')});
			return false;
		}
	);
}*/

function error(msg) {
	$("body").html("<div class='error-msg'><img src='info.png' style='width: 40px; vertical-align: middle; margin-right: 8px;' />" + msg + "</div>");
}

function get_ranks() {
	console.log('making request...');
	$.ajax({
		type: 'POST',
		url: PUSH_URL,
		data: JSON.stringify({securitykey: localStorage.securitykey}),
		contentType: 'application/json',
		error: function(xhr, statusText, errorThrown) { 
			chrome.browserAction.setBadgeText({text: 'net'});
			error(DEF_ERROR_MSG);
		},
		success: function(data) {
			switch(data['status']) {
				case SUCCESS:
					$("#loader").toggle();
					res = data['result'];
					for(var i = 0; i < res.length; i++) {
						var cluster_html = "<ul class='cluster' id='" + res[i]['id'] + "'>";
						children = res[i]['cluster'];
						for(var j = 0; j < children.length; j++)
							cluster_html += "<li><a href='#'>" + children[j] + "</a></li>";
						cluster_html += "</ul>";
						$("body").append(cluster_html);
					}
					chrome.browserAction.setBadgeText({text: ''});
					break;
				case SERVER_ERROR:
					error(data['message']);
					break;
				case INVALID_KEY:
					chrome.browserAction.setBadgeText({text: 'key'});
					error(KEY_ERROR_MSG);
					break;
				case IN_PROGRESS:
					error(data['message']);
					break;
				case INSUFFICIENT_DATA:
					error(data['message']);
					break;
				default:
					console.log(data['status'] + ": unknown error");
					error(data['message']);
					break;
			}
		}
	});
}
