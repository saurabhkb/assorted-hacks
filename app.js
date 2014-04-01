/**
 * Module dependencies.
 */

var express = require('express')
	, routes = require('./routes')
	, stylus = require('stylus')
	, nib = require('nib')
	, sio = require('socket.io')
	, url = require('url')
	, state_secret = SECRET
	, RedisStore = require('connect-redis')(express)
	, parseCookie = require('connect').utils.parseSignedCookie
	, rtg = url.parse(REDIS_URL)
	, redis = require('redis').createClient(rtg.port, rtg.hostname)
//	, redis = require('redis').createClient()
	, STORE = new RedisStore({client: redis});
redis.auth(rtg.auth.split(':')[1]);
pg = require('pg');
var app = express.createServer();
conString = PG_CONN;
// Configuration
app.configure('development', function(){
	app.use(stylus.middleware({
		src: __dirname +'/public/',
		compile: function(str, path){
				return stylus(str).set('filename', path).set('compress', true).use(nib());
			}
	}));
	app.set('views', __dirname + '/views');
	app.set('view engine', 'jade');
	app.set('view options', {layout: false});
	app.use(express.bodyParser({keepExtensions: true, uploadDir: __dirname + '/public/uploads'}));
	app.use(express.cookieParser());
	app.use(express.session({store: STORE, secret: state_secret, key: "express.sid"}));
	app.use(express.methodOverride());
	app.use(express.static(__dirname + '/public/'));
	app.use(app.router);
//	app.use(express.errorHandler({ dumpExceptions: true, showStack: true }));
});
/*app.configure('production', function(){
	app.use(express.errorHandler());
});*/

app.configure('production', function(){
	app.use(stylus.middleware({
		src: 'https://s3.amazonaws.com/radiant-sky/public/',
		compile: function(str, path){
				return stylus(str).set('filename', path).set('compress', true).use(nib());
			}
	}));
	app.set('views', __dirname + '/views');
	app.set('view engine', 'jade');
	app.set('view options', {layout: false});
	app.use(express.bodyParser({keepExtensions: true}));
	app.use(express.cookieParser());
	app.use(express.session({store: STORE, secret: state_secret, key: "express.sid"}));
	app.use(express.methodOverride());
	app.use(express.static(__dirname + '/public'));
	app.use(app.router);
});


// Middleware
function userAuth(req, res, next){
	res.header('Cache-Control', 'no-cache, private, no-store, must-revalidate, max-stale=0, post-check=0, pre-check=0');
	if(req.session.is_logged_in === true)
	{
		req.session.current_course = req.params.course_id || "";
		if(req.session.current_course && req.session.user.user_id){
			pg.connect(conString, function(err, client){
				if(err) throw err;
				client.query('SELECT courses.*, user_course.role FROM courses LEFT JOIN user_course ON courses.course_id = user_course.course_id AND user_id = $1 WHERE courses.course_id = $2', [req.session.user.user_id, req.session.current_course], function(err, result){
					if(err) throw err;
					if(result.rows[0])
					{
						req.coursedet = result.rows[0];
						if(req.coursedet.role == null) req.coursedet.role = -1;
						next();
					}
					else{
						res.render('page_not_found');
					}
				});
			});
		}else{
			next();
		}
	}
	else{
		res.redirect('/');
	}
}

function loadUser(req, res, next){
	
	var eid = req.body.user.emailid || "";
	var pwd = req.body.user.password || "";
	pg.connect(conString, function(err, client){
		if(err) throw err;
		client.query('SELECT * FROM "user" WHERE email_id = $1 AND password = $2', [eid, pwd], function(err, result){
			if(err) throw err;
			console.log(result);
			console.log(JSON.stringify(result.rows[0]));
			if(result.rows[0]){
				req.session.user = result.rows[0];
				client.query('UPDATE "user" SET "sessionID" = $1 WHERE user_id = $2', [req.sessionID, req.session.user.user_id], function(err, result){
					if(err) throw err;
					client.query('SELECT course_name, courses.course_id, course_label, course_key, course_desc, user_course.role  FROM courses INNER JOIN user_course ON courses.course_id = user_course.course_id WHERE user_id = $1 ORDER BY course_name ASC', [req.session.user.user_id], function(err, result){
						if(err) throw err;
						req.session.courses = result.rows || [];
						req.session.is_logged_in = true;
						next();
					});
				});
			}else res.redirect("/");
		});
	});
}

function killSession(req, res, next){
	pg.connect(conString, function(err, client){
		if(err) throw err;
		client.query('UPDATE "user" SET "sessionID" = 0, "socketID" = 0 WHERE user_id = $1', [req.session.user.user_id], function(err, result){
			if(err) throw err;
			req.session.is_logged_in = false;
			req.session.user = "";
			req.session.courses = "";
			req.session.destroy(function(err){});
			next();
		});
	});
}
function getNotifications(req, res, next){
	if(req.session.courses.length > 0){
		pg.connect(conString, function(err, client){
			if(err) throw err;
			var query = 'SELECT id, type, courses.course_id, source_id, to_char(to_timestamp(timestamp), \'HH12:MM am D,mon YYYY\') as timestamp, reference, first_name, last_name, user_id, img_id, course_name  FROM (SELECT notifications.*, "user".*, notif_view.seen FROM (notifications INNER JOIN "user" ON source_id = user_id) INNER JOIN notif_view ON notifications.id = notif_view.notif_id AND notif_view.user_id = ' + req.session.user.user_id + ') as T INNER JOIN courses ON T.course_id = courses.course_id  WHERE (';
			var i = 0;
			for(i = 0; i < req.session.courses.length - 1; i++)
				query += ' courses.course_id = ' + req.session.courses[i].course_id + ' OR ';
			query += ' courses.course_id = ' + req.session.courses[i].course_id + ') AND user_id != ' + req.session.user.user_id + ' ORDER BY timestamp DESC LIMIT 8';
			client.query(query, [], function(err, result){
				if(err) throw err;
				req.notifications = result.rows;
				next();
			});
		});
	}else{
		req.notifications = [];
		next();
	}
}
//UPDATE NOTIFICATIONS DATABASE
function addNotification(type, course_id, source_id, timestamp, ref_id){
	pg.connect(conString, function(err, client){
		if(err) throw err;
		client.query('INSERT INTO notifications (type, course_id, source_id, timestamp, reference) VALUES ($1, $2, $3, $4, $5) RETURNING id', [type, course_id, source_id, timestamp, ref_id], function(err, result){
			if(err) throw err;
			client.query('INSERT INTO notif_view (user_id, notif_id, seen) SELECT "user".user_id, $1, 0 FROM "user" INNER JOIN user_course ON "user".user_id = user_course.user_id WHERE course_id = 1', [result.rows[0].id], function(err, result){if(err) throw err;});
		});
	});
}

function sendToClientList(course_id, user_id, func){
	pg.connect(conString, function(err, client){
		if(err) throw err;
		client.query('SELECT "socketID" FROM "user" INNER JOIN user_course ON "user".user_id = user_course.user_id WHERE course_id = $1 AND "socketID" != 0 AND "sessionID" != "0" AND "user".user_id != $1', [course_id, user_id], function(err, result){
			if(err) throw err;
			if(result.rows.length > 0)
				func(result.rows);
			else return;
		});
	});
}
	

function createUser(req, res, next){
	var fn = req.body.user.fn;
	var ln = req.body.user.ln;
	var emid = req.body.user.emid;
	var pwd = req.body.user.pwd;
	if(!fn || !ln || !emid || !pwd || !fn.trim() || !ln.trim() || !emid.trim() || !pwd.trim())
		res.redirect('/');
	else{
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('INSERT INTO "user" (first_name, last_name, email_id, password, masthead_img, college, "sessionID", "socketID") VALUES ($1, $2, $3, $4, \'default.jpg\', \'null\', \'0\', \'0\') RETURNING user_id', [fn, ln, emid, pwd], function(err, result){
				if(err) throw err;
				req.session.is_logged_in = true;
				req.session.user = {user_id: result.rows[0].user_id, first_name: fn, last_name: ln, email_id: emid, masthead_img: 'default.jpg', sessionID: req.sessionID, img_id: 'default.jpg'};
				req.session.courses = [];
				client.query('UPDATE "user" SET "sessionID" = $1 WHERE user_id = $2', [req.sessionID, req.session.user.user_id], function(err, result){if(err) throw err; next();});
			});
		});
	}
}

function redirect_if_auth(req, res, next){
	if(req.session.is_logged_in && req.session.user){
		res.redirect("/user/home");
	}
	else{
		next();
	}
}

// Routes
app.get('/', redirect_if_auth, routes.index);
app.get('/user', userAuth, function(req, res){res.redirect('/user/home');});
app.get('/user/home', userAuth, getNotifications, routes.home);
app.get('/logout', killSession, function(req, res){res.header('Cache-Control', 'no-cache, private, no-store, must-revalidate, max-stale=0, post-check=0, pre-check=0');res.redirect('/');});
app.post('/signin', loadUser, function(req, res){res.redirect('/user/home');});
app.post('/signup', createUser, function(req, res){res.redirect('/user/home');});
app.get('/create_course', userAuth, getNotifications, routes.create_course_view);
app.get('/chat/', function(req, res){res.render('chat', {layout: false});});
app.get('/courses/:course_id/', userAuth, getNotifications, function(req, res){res.redirect('/courses/' + req.params.course_id + '/main/')});
app.get('/courses/:course_id/:portal/', userAuth, getNotifications, routes.coursepage);
app.post('/courses/:course_id/edit/', userAuth, getNotifications, routes.course_edit);
app.all('/courses/:course_id/:portal/:option', userAuth, getNotifications, routes.extraoptions);
app.post('/courses/:course_id/assignments/:a_id/comments/', userAuth, getNotifications, routes.comments);
app.post('/courses/:course_id/assignments/:a_id/update_mks/', userAuth, getNotifications, routes.update_mks);
app.get('/courses/:course_id/assignments/:a_id/instr', userAuth, getNotifications, routes.assignment_det);
app.get('/courses/:course_id/people/:person_id/instr', userAuth, getNotifications, routes.person_interac);
app.get('/user/profile', userAuth, getNotifications, routes.profile);
app.post('/user/profile/edit', userAuth, getNotifications, routes.editprofile);
app.get('/user/:user_id/', userAuth, getNotifications, routes.userpage);
app.get('/user/:user_id/:portal', userAuth, getNotifications, routes.userpage);
app.get('/public/files/:file_name', userAuth, getNotifications, function(req, res){res.download('/files/' + req.params.file_name);});
app.get('/public/submissions/:file_name', userAuth, getNotifications, function(req, res){res.download('/submissions/' + req.params.file_name);});
app.get('/search/', userAuth, getNotifications, routes.searchpage);
app.post('/notif_complete', userAuth, getNotifications, routes.notif);
app.post('/new_course/', userAuth, getNotifications, routes.addcourse);
app.post('/course_key/', userAuth, getNotifications, routes.generate_id);
app.post('/join_course/', userAuth, getNotifications, routes.joincourse);
app.get('*', userAuth, function(req, res){res.render('page_not_found');});
app.get('/error_page', function(req, res){res.render('error_page');});
//app.error(function(err, req, res){if(err){console.log("app error: " + err); res.redirect('/error_page');}});

var port = process.env.PORT || 3000;
app.listen(port, function(){
  console.log('Express server listening on port %d in %s mode', app.address().port, app.settings.env);
});

/*SOCKET.IO SERVER*/
var io = sio.listen(app);

io.configure('production', function(){
	io.set('transports', ['xhr-polling']);
	io.set('polling duration', 10);
	io.enable('browser client minification');
	io.enable('browser client etag');
	io.enable('browser client gzip');
	io.set('log level', 1);
});
/*ENABLING SESSION ACCESS THROUGH SOCKET TO VERIFY SOURCE USER, ETC.*/
io.set('authorization', function(data, accept){
	if(data.headers.cookie){
		data.cookie = parseCookie(data.headers.cookie);
		console.log("data.cookie: " + data.cookie);
		data.sessionID = decodeURIComponent((data.cookie).split("=")[1]);
		console.log("session id: " + data.sessionID);
		console.log("data.sessionID: " + data.sessionID);
		redis.keys("*", function(err, rows){
			if(err) throw err;
			for(var i = 0; i < rows.length; i++)
				redis.get(rows[i], function(err, dat){if(err) throw err; console.log("val: " + dat);});
			console.log("keys: " + JSON.stringify(rows));
		});
		redis.get("sess:" + data.sessionID, function(err, session){
			if(err || !session){
				console.log("error: " + err);
				console.log("session: " + session);
				accept('error!', false);
			}else{
				data.session = JSON.parse(session);
				accept(null, true);
			}
		});
	}
	else{
		return accept('No cookie transmitted', false);
	}
});

/*ON SOCKET CONNECT BEHAVIOUR*/

//notifications socket channel
io.of('/notifications').on('connection', function(notif_sock){
	notif_sock.on('notification', function(json){
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('INSERT INTO posts (course_id, author_id, post_content, post_timestamp) VALUES ($1, $2, $3, $4)', [msg_obj.course_id, socket.handshake.session.user.user_id, msg_obj.post_content, msg_obj.post_timestamp], function(err, results){
				notif_sock.emit('notification', 0, '{a: b}');
			});
		});
	});
	notif_sock.on('disconnect', function(){
		console.log('disconnected!');
	});
});

//stream posts socket channel
io.of('/streamposts').on('connection', function(str_sock){
	console.log('id: ' + str_sock.id);
	pg.connect(conString, function(err, client){
		if(err) throw err;
		client.query('UPDATE "user" SET "socketID" = $1 WHERE user_id = $2', [str_sock.id, str_sock.handshake.session.user.user_id], function(err, result){if(err) throw err;});
	});
	/*STREAM POSTS SOCKET BEHAVIOUR*/
	str_sock.on('user post', function(msg_json){
		var msg_obj = JSON.parse(msg_json);
		msg_obj.post_timestamp = new Date().getTime() / 1000;
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('INSERT INTO posts (course_id, author_id, post_content, post_timestamp) VALUES ($1, $2, $3, $4) RETURNING id', [msg_obj.course_id, str_sock.handshake.session.user.user_id, msg_obj.post_content, msg_obj.post_timestamp], function(err, result){
				if(err) throw err;
				addNotification('STREAM', msg_obj.course_id, str_sock.handshake.session.user.user_id, msg_obj.post_timestamp, result.rows[0].id);
				client.query('SELECT * FROM courses WHERE course_id = $1', [msg_obj.course_id], function(err, result){
					if(err) throw err;
					if(result.rows[0])
					{
						var obj =  str_sock.handshake.session.user;
						obj += result.rows[0];
						console.log('JS OBJ: ' + JSON.stringify(obj));
						sendToClientList(msg_obj.course_id, str_sock.handshake.session.user.user_id, function(cli){for(var i = 0; i < cli.length; i++) io.of('/streamposts').socket(cli[i].socketID).emit('notification', JSON.stringify(str_sock.handshake.session.user), JSON.stringify(obj));});
					}
				});
				sendToClientList(msg_obj.course_id, str_sock.handshake.session.user.user_id, function(cli){for(var i = 0; i < cli.length; i++) io.of('/streamposts').socket(cli[i].socketID).emit('user post', JSON.stringify(str_sock.handshake.session.user), msg_json);});
			});
		});
	});

	/*ON SOCKET DISCONNECT BEHAVIOUR*/
	str_sock.on('disconnect', function(){
		console.log('disconnected!');
	});
});
io.of('/assignments').on('connection', function(assgn_sock){
	assgn_sock.on('assignment', function(a_json){
		var a_obj = JSON.parse(a_json);
		a_obj.creation_date = new Date().getTime() / 1000;
		var course_id = assgn_sock.handshake.session.current_course;
		var assgn_title = a_obj.assgn_title; console.log(assgn_title);
		var assgn_content = a_obj.assgn_content;
		var sdate = new Date(a_obj.sdate).getTime() / 1000;
		var edate = new Date(a_obj.edate).getTime() / 1000;
		var cdate = new Date().getTime() / 1000;
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('INSERT INTO assignments (course_id, assignment_title, assignment_content, start_date, end_date, creation_date) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id', [course_id, assgn_title, assgn_content, sdate, edate, cdate], function(err, result){
				if(err) throw err;
				addNotification('ASSIGNMENT', a_obj.course_id, assgn_sock.handshake.session.user.user_id, cdate, result.rows[0].id);
				client.query('SELECT * FROM courses WHERE course_id = $1', [a_obj.course_id], function(err, result){
					/*TODO check this behaviour, ensure that data is being sent only where it needs to be*/
					if(err) throw err;
					if(result.rows[0])
					{
						var obj =  assgn_sock.handshake.session.user;
						obj += result.rows[0];
						console.log(JSON.stringify(obj));
						assgn_sock.broadcast.emit('notification', JSON.stringify(assgn_sock.handshake.session.user), JSON.stringify(obj));
					}
				});
				assgn_sock.emit('assignment', JSON.stringify(assgn_sock.handshake.session.user), a_json, result.rows[0].id);
			});
		});
	});

});
io.of('/assignment_comments').on('connection', function(com_sock){
	/*ASSIGNMENT COMMNETS SOCKET BEHAVIOUR*/
	com_sock.on('assignment comment', function(com_json){
		var com_obj = JSON.parse(com_json);
		console.log(JSON.stringify(com_obj));
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('INSERT INTO a_comments (assignment_id, author_id, comment, time, assignment_source) VALUES ($1, $2, $3, $4, $5)', [com_obj.a_id, com_sock.handshake.session.user.user_id, com_obj.comment, new Date() / 1000, com_obj.target_id], function(err, result){
				if(err) throw err;
				//result.insertId contains primary key index
				/*
				addNotification('STREAM', msg_obj.course_id, str_sock.handshake.session.user.user_id, msg_obj.post_timestamp, result.insertId);
				client.query('SELECT * FROM courses WHERE course_id = ?', [msg_obj.course_id], function(err, rows, fields){
					/*TODO check this behaviour, ensure that data is being sent only where it needs to be
					if(err) throw err;
					if(rows[0])
					{
						var obj =  str_sock.handshake.session.user;
						obj += rows[0];
						str_sock.broadcast.emit('notification', JSON.stringify(str_sock.handshake.session.user), JSON.stringify(obj));
					}
					client.end();
				});*/
	//			com_sock.broadcast.emit('assignment comment', JSON.stringify(str_sock.handshake.session.user), msg_json);
			});
		});
	});

	/*ON SOCKET DISCONNECT BEHAVIOUR*/
	com_sock.on('disconnect', function(){
		console.log('disconnected!');
	});
});

