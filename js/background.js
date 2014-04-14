/* constants repeated */

/* base */
//var HOST = 'http://powerful-falls-2602.herokuapp.com';
var HOST = 'http://localhost:5000';
var SYNC_URL = HOST + '/sync_history';
var PUSH_URL = HOST + '/push';

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


chrome.alarms.create(TIMER, {'delayInMinutes': 0, 'periodInMinutes': INTERVAL / (60 * 1000)});
chrome.runtime.onInstalled.addListener(function() {
	localStorage.hist_list = "[]";
	console.log("installed");
});


chrome.alarms.onAlarm.addListener(function(alarm) {
	hist_list = JSON.parse(localStorage.hist_list);
	if(alarm.name == TIMER && hist_list.length > 0)
		syncHist(function(a) {}, "");
});

function pushHist(elem) {
	jarray = JSON.parse(localStorage.hist_list);
	jarray.push(elem);
	localStorage.hist_list = JSON.stringify(jarray);
}

chrome.runtime.onMessage.addListener(
	function(request, sender, sendResponse) {
		console.log('request: ' + JSON.stringify(request));
		hist_list = JSON.parse(localStorage.hist_list);
		if(hist_list.length > MAX_HIST)
			syncHist(pushHist, request);
		else pushHist(request);
	}
);


function syncHist(callback, arg) {
	console.log('adding securitykey: ' + localStorage.securitykey);
	chrome.browserAction.setBadgeText({text: 'sync'});
	$.ajax({
		type: 'POST',
		url: SYNC_URL,
		data: JSON.stringify({
			'securitykey': localStorage.securitykey,
			'history': JSON.parse(localStorage.hist_list)
		}),
		contentType: "application/json",
		error: function(xhr, statusText, errorThrown) {
			chrome.browserAction.setBadgeText({text: 'net'});
		},
		success: function(d) {
			switch(d['status']) {
				case SUCCESS:
					chrome.browserAction.setBadgeText({text: ''});
					localStorage.hist_list = "[]";
					console.log('sync complete!');
					break;
				case SERVER_ERROR:
					chrome.browserAction.setBadgeText({text: 'net'});
					console.log(d['message']);
					break;
				case INVALID_KEY:
					chrome.browserAction.setBadgeText({text: 'key'});
					break;
				case IN_PROGRESS:
					break;
				case INSUFFICIENT_DATA:
					chrome.browserAction.setBadgeText({text: 'data'});
					break;
				default:
					console.log(d['status'] + ": unknown error");
					break;
			}
			callback(arg);
		}
	});
}
