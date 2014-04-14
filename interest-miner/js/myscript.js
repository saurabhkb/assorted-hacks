//if(window.location.host && document.title) {	/* for real */
if(window.location.host) {
	console.log('sending data: ' + JSON.stringify({'url': window.location.host, 'title': document.title, 'ts': new Date().getTime()}));
	chrome.runtime.sendMessage(
		{'url': window.location.host, 'title': document.title, 'ts': new Date().getTime()}, function(response) {console.log(response);}
	);
}
