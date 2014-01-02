var pusher = new Pusher('754be4ab2d0de2d2272b');
var channel = pusher.subscribe('alert_channel');

channel.bind('status_update', function(data) {
	//update chart here. data.hospital_id, data.bed_change
	alert(data.hospital_id + ", " + data.bed_change);
});

// Enable pusher logging - don't include this in production
//Pusher.log = function(message) {
//		if (window.console && window.console.log) {
//		window.console.log(message);
//	}
//};
