/* base */
var HOST = 'http://localhost:5000';
//var HOST = 'http://powerful-falls-2602.herokuapp.com';
var SYNC_URL = HOST + '/sync_history';
var PUSH_URL = HOST + '/push';

/*constants*/
var INTERVAL = 1000 * 60 * 60 * 24 * 7;		//range = 1 week
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
