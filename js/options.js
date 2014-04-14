/* base */
var HOST = 'http://powerful-falls-2602.herokuapp.com';
var SYNC_URL = HOST + '/sync_history';
var PUSH_URL = HOST + '/push';
var EMAIL_URL = HOST + '/email';
var HASH_URL = HOST + '/hash';

/*constants*/
var INTERVAL = 1000 * 60 * 60 * 24;		//range = 1 week
var MAX_HIST = 5;				//max no of intervals in the past to mine up to
var TIMER = 'timer';

var DEF_ERROR_MSG = 'Could not connect to server!';
var KEY_ERROR_MSG = 'Please generate a security key by going to the options page!';

/* status */
var SUCCESS = 0;
var SERVER_ERROR = 1;
var INVALID_KEY = 2;
var IN_PROGRESS = 3;
var INSUFFICIENT_DATA = 4;

$("document").ready(
	function() {
		$.ajax({
			type: 'post',
			url: EMAIL_URL,
			data: {action: 'get_last_update', securitykey: localStorage.securitykey},
			success: function(d) {
				if(d['status'] == SUCCESS) {
					email = d['email'];
					ts = parseInt(d['timestamp']);
					$("#log").html("<p>" + email + "</p><p>" + new Date(ts * 1000).toDateString() + "</p>");
				} else if(d['status'] == INVALID_KEY) {
					alert("Invalid key!");
				}
			},
			error: function(xhr, error, stat) {}
		});
		$("#key").val(localStorage.securitykey);
		$("#hashform").submit(
			function(e) {
				salt = $("#salt").val();
				$("#salt").val("");
				e.preventDefault();
				$.ajax({
					type: 'post',
					url: HASH_URL,
					data: {securitykey: localStorage.securitykey, salt: salt},
					success: function(hash) {
						if(hash['status'] == SUCCESS) {
							localStorage.securitykey = hash['securitykey'];
							$("#key").val(hash['securitykey']);
						} else if(hash['status'] == INVALID_KEY) {
							alert("Invalid key!");
						}
					},
					error: function(xhr, error, stat) {alert(error);}
				});
			}
		);
		$("#firsthashform").submit(
			function(e) {
				email = $("#email").val();
				e.preventDefault();
				if(!email || !email.trim()) {
					$("#email").val("").focus();
					return;
				}
				$("#email_load").toggle();
				securitykey = localStorage.securitykey || "";
				$.ajax({
					type: 'post',
					url: EMAIL_URL,
					data: {action: 'generate_email', email: email, securitykey: securitykey},
					success: function(ret) {
						$("#email_load").toggle();
						if(ret['status'] == SUCCESS) {
							alert("A key has been sent to your email address");
						} else if(ret['status'] == INVALID_KEY) {
							alert("Invalid key!");
						} else if(ret['status'] == SERVER_ERROR) {
							alert(ret['message']);
						}
					},
					error: function(xhr, error, stat) {
						$("#email_load").toggle();
						alert(error);
					}
				});
			}
		);

		$("#confirm").submit(
			function(e) {
				key = $("#firstkey").val();
				e.preventDefault();
				if(!key || !key.trim()) {
					$("#firstkey").val("").focus();
					return false;
				} else {
					$.ajax({
						type: 'post',
						url: EMAIL_URL,
						data: {action: 'verify_key', securitykey: key},
						success: function(ret) {
							if(ret['status'] == SUCCESS) {
								localStorage.securitykey = ret['securitykey'];
								$("#key").val(ret['securitykey']);
								chrome.browserAction.setBadgeText({'text': ''});
								alert("Key verified!");
							} else if(ret['status'] == INVALID_KEY) {
								alert("Invalid key!");
							} else if(ret['status'] == SERVER_ERROR) {
								alert(ret['message']);
							}
						},
						error: function(xhr, error, stat) {alert(error);}
					});
				}
			}
		);

	}
);
