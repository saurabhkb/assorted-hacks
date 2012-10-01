/*
 * GET home page.
 */

exports.index = function(req, res){
	res.render('index', { title: 'Radiant Sky' });
};

exports.home = function(req, res){
	res.render('home', {loc: 'home', course_data: req.session.courses, me: req.session.user, notif: req.notifications});
};
function addNotification(type, course_id, source_id, timestamp, ref_id){
	pg.connect(conString, function(err, client){
		if(err) throw err;
		client.query('INSERT INTO notifications (type, course_id, source_id, timestamp, reference) VALUES ($1, $2, $3, $4, $5)', [type, course_id, source_id, timestamp, ref_id], function(err, result){
			if(err) throw err;
		});
	});
}

function genId(length){
	var chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', returnValue = '', x, i;
	for (x = 0; x < length; x += 1){
		i = Math.floor(Math.random() * 62);
		returnValue += chars.charAt(i);
	}
	return 'ID_' + returnValue;
}
function genSpecialId(length){
	var chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', returnValue = '', x, i;
	for (x = 0; x < length; x += 1){
		i = Math.floor(Math.random() * 62);
		returnValue += chars.charAt(i);
	}
	return returnValue;
}
//DISPLAY COURSE VIEW ACCORDING TO PORTAL SELECTED
exports.coursepage = function(req, res){
	var cid = req.params.course_id;
	var p = req.params.portal;
	var course_det = req.coursedet;
	var r = req.coursedet.role;
	if(p == 'main' || p == ''){
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('SELECT id, course_id, author_id, post_content, to_char(to_timestamp(post_timestamp), \'HH12:MM am D,mon YYYY\') as post_timestamp, "user".* FROM posts INNER JOIN "user" ON author_id = user_id WHERE course_id = $1 ORDER BY post_timestamp DESC', [course_det.course_id], function(err, result){
			if(err) throw err;
			res.render('mainpage', {loc: course_det, course_data: req.session.courses, portal: p, me: req.session.user, prev_posts: result.rows, role: r, notif: req.notifications});});
		});
	}
	else if(p == 'assignments'){
		if(r == 0){
			pg.connect(conString, function(err, client){
				if(err) throw err;
				client.query('select id, course_id, assignment_title, assignment_content, to_char(to_timestamp(start_date), \'HH12:MM am D,mon YYYY\') as start_date, to_char(to_timestamp(end_date), \'HH12:MM am D,mon YYYY\') as end_date, total_marks, to_char(to_timestamp(submission_date), \'HH12:MM am D,mon YYYY\') as submission_date, user_id, filename, marks, submission_id, assignment_id from assignments left join (select * from submissions where user_id = $1) as t on id = assignment_id where course_id = $2', [req.session.user.user_id, course_det.course_id], function(err, result){
					if(err) throw err;
					res.render('assgnpage_instr', {loc: course_det, course_data: req.session.courses, portal: p, me: req.session.user, assgns: result.rows, role: r, notif: req.notifications});
				});
			});
		}
		else if(r == 1){
			pg.connect(conString, function(err, client){
				if(err) throw err;
				client.query('SELECT id, course_id, assignment_title, assignment_content, to_char(to_timestamp(start_date), \'HH12:MM am D,mon YYYY\') as start_date, to_char(to_timestamp(end_date), \'HH12:MM am D,mon YYYY\') as end_date, total_marks FROM assignments  WHERE course_id = $1 ORDER BY creation_date ASC', [course_det.course_id], function(err, result){
					if(err) throw err;
					res.render('assgnpage_instr', {loc: course_det, course_data: req.session.courses, portal: p, me: req.session.user, assgns: result.rows, role: r, notif: req.notifications});
				});
			});
		}
		else if(r == -1){
			pg.connect(conString, function(err, client){
				if(err) throw err;
				client.query('SELECT id, course_id, assignment_title, assignment_content, to_char(to_timestamp(start_date), \'HH12:MM am D,mon YYYY\') as start_date, to_char(to_timestamp(end_date), \'HH12:MM am D,mon YYYY\') as end_date FROM assignments WHERE course_id = $1 ORDER BY creation_date ASC', [course_det.course_id], function(err, result){
					if(err) throw err;
					res.render('assgnpage_instr', {loc: course_det, course_data: req.session.courses, portal: p, me: req.session.user, assgns: result.rows, role: r, notif: req.notifications});
				});
			});
		}
	}
	else if(p == 'calendar'){
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('SELECT * FROM assignments WHERE course_id = $1 ORDER BY creation_date ASC', [course_det.course_id], function(err, result){
					if(err) throw err;
					res.render('calendarpage', {loc: course_det, course_data: req.session.courses, portal: p, me: req.session.user, role: r, notif: req.notifications, assgns: result.rows});
			});
		});
	}
	else if(p == 'people'){
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('SELECT * FROM user_course INNER JOIN "user" ON user_course.user_id = "user".user_id WHERE course_id = $1 ORDER BY role DESC', [course_det.course_id], function(err, result){
				if(err) throw err;
				res.render('people_instr', {loc: course_det, course_data: req.session.courses, portal: p, me: req.session.user, role: r, people: result.rows, notif: req.notifications});
			});
		});
	}
	else if(p == 'resources'){
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('SELECT id, course_id, to_char(to_timestamp(upload_date), \'HH12:MM am D,mon YYYY\') as upload_date, filename, explanation, filetype, "user".* FROM resources INNER JOIN "user" ON resources.user_id = "user".user_id WHERE course_id = $1 ORDER BY upload_date DESC', [course_det.course_id], function(err, res_result){
				if(err) throw err;
				client.query('SELECT "user".*, link_id, link_type, link_url, link_name, course_id, to_char(to_timestamp(upload_date), \'HH12:MM am D,mon YYYY\') as upload_date, explanation FROM resource_links INNER JOIN "user" ON resource_links.user_id = "user".user_id WHERE course_id = $1 ORDER BY upload_date DESC', [course_det.course_id], function(err, link_result){
					if(err) throw err;
				res.render('resource_instr', {loc: course_det, course_data: req.session.courses, portal: p, me: req.session.user, role: r, resources: res_result.rows, links: link_result.rows, notif: req.notifications});
				});
			});
		});
	}
	else if(p == 'admin'){
		res.render('course_admin', {loc: course_det, course_data: req.session.courses, portal: p, me: req.session.user, role: r, notif: req.notifications});
	}
	else
		res.render('coursepage', {loc: course_det, course_data: req.session.courses, portal: p, me: req.session.user, role: r, notif: req.notifications});
}
exports.create_course_view = function(req, res){
	res.render('create_course', {me: req.session.user, loc: 'create_course', course_data: req.session.courses, notif: req.notifications});
};
exports.addcourse = function(req, res){
	var name = req.body.cname;
	var desc = req.body.cdesc;
	var clab = req.body.clab
	var ckey = req.body.ckey;
	if(!name || !clab || !ckey || !name.trim() || !clab.trim() || !ckey.trim())
		res.redirect('/create_course');
	else{
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('INSERT INTO courses (course_label, course_name, course_desc, course_key) VALUES ( $1, $2, $3, $4 ) RETURNING course_id', [clab, name, desc, ckey], function(err, results){
				if(err) throw err;
				var id = results.rows[0].course_id;
				client.query('INSERT INTO user_course (user_id, course_id, role) VALUES ($1, $2, 1)', [req.session.user.user_id, id], function(err, result){
					if(err) throw err;
					req.session.courses.push({course_id: id, course_name: name, course_label: clab, course_desc: desc, course_key: ckey, role: 1});
					res.redirect('/courses/' + id + '/main/');
				});
			});
		});
	}
}
exports.userpage = function(req, res){
	var user_id = req.params.user_id;
	if(user_id == req.session.user.user_id)
		res.redirect('/user/profile');
	var portal = req.params.portal;
	portal = portal || '';
	pg.connect(conString, function(err, client){
		if(err) throw err;
		client.query('SELECT * FROM "user" WHERE user_id = $1', [user_id], function(err, result){
			if(err) throw err;
			if(!result.rows[0]) res.render('page_not_found');
			else{
				var userdet = result.rows[0];
				res.render('userpage', {me: req.session.user, user: userdet, course_data: req.session.courses, portal: portal, notif: req.notifications});
			}
		});
	});
}

exports.assignment_det = function(req, res){
	var user_id = req.session.user.user_id;
	var course_id = req.params.course_id;
	var a_id = req.params.a_id;
	if(req.coursedet.role != 1)
		res.render('permission');
	else{
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('select first_name, last_name, T.user_id, img_id, submission_id, to_char(to_timestamp(submission_date), \'HH12:MM am DD, month YYYY\') as submission_date, filename from (select "user".* from user_course inner join "user" on user_course.user_id = "user".user_id where course_id = $1 and role = 0) as T left join submissions on T.user_id = submissions.user_id and (assignment_id = $2 or assignment_id is null)', [course_id, a_id], function(err, result){
				if(err) throw err;
				client.query('SELECT id, course_id, assignment_title, assignment_content, to_char(to_timestamp(start_date), \'HH12:MM am DD, month YYYY\') as start_date, to_char(to_timestamp(end_date), \'HH12:MM am DD, month YYYY\') as end_date, total_marks FROM assignments WHERE id = $1', [a_id], function(err, assg_res){
					if(err) throw err;
					if(assg_res.rows[0])
						res.render('assignment_details', {me: req.session.user, course_data: req.session.courses, assgn_data: result.rows, loc: req.coursedet, notif: req.notifications, portal: 'assignments', role: 1, assg: assg_res.rows[0]});
				});
			});
		});
	}
}
exports.comments = function(req, res){
	var uid = req.body.user_id;
	var aid = req.params.a_id;
	if(req.session.user.user_id == uid || req.coursedet.role == 1){
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('SELECT * FROM a_comments INNER JOIN "user" ON author_id = user_id WHERE assignment_source = $1 AND assignment_id = $2', [uid, aid], function(err, result){
				if(err) throw err;
				res.send(JSON.stringify(result.rows));
			});
		});
	}
	else res.send(null);
}
exports.profile = function(req, res){
	var p = req.params.portal;
	var user_id = req.session.user.user_id;
	res.render('profile', {loc: 'profile', me: req.session.user, course_data: req.session.courses, portal: p, notif: req.notifications});
};
exports.editprofile = function(req, res){
	var fn = req.body.fn;
	var ln = req.body.ln;
	var emid = req.body.emid;
	var bgimg = req.files.img || '';
	console.log(bgimg);
	req.session.user.first_name = fn;
	req.session.user.last_name = ln;
	req.session.email_id = emid;
	var file_upload = false;
	var id = genId(20);
	var name = '';
	if(bgimg && bgimg.size && bgimg.filename && bgimg.name){
		var ext = bgimg.type;
		var type = '';
		switch(ext){
			case 'image/png':
				type = 'png';
				break;
			case 'image/jpeg':
				type = 'jpeg';
				break;
			case 'image/gif':
				type = 'gif';
				break;
			case 'image/svg':
				type = 'svg';
				break;
		}
		if(type != ''){
			var tmp_path = bgimg.path;
			name = id + '.' + type;
			req.session.user.img_id = name;
			var init_target_path = 'public/images/user/post/' + name;
			console.log(tmp_path + ', ' + init_target_path);
			var im = require('imagemagick');
			im.resize({srcPath: tmp_path, dstPath: tmp_path, width: 40}, function(err, stdout, stderr){
				if(err) throw err;
				console.log(stdout);
				var knoxCli = require('knox').createClient({
					key: "AKIAJCRRUWJ6DKKLKCXQ",
					secret: "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",
					bucket: "radiant-sky"
				});
				knoxCli.putFile(tmp_path, init_target_path, {'Content-Type': 'image/' + type}, function(err, res){
					if(err) throw err; console.log("RES: " + res.statusCode);
					var tmp_url = "https://s3.amazonaws.com/radiant-sky/public/images/user/temp/" + name;
					var final_target_path = "public/images/user/profile/" + name;
					/*var command = 'curl "http://api.blitline.com/job" -d json=\'{ "application_id": "-LQ8fOpNSGbUnVnhCadifQ", "src" : "' + tmp_url + '", "functions" : [ {"name": "resize_to_fit", "params" : {"width" : 40, "height" : 40}, "save" : { "image_identifier" : "MY_CLIENT_ID", "s3_destination":{"bucket":"radiant-sky", "key":"' + final_target_path + '" }}} ]}\'';
					child = require('child_process').exec(command, function(err, stdout, stderr){
						console.log(stdout + stderr);
						console.log("ERROR: " + err);
					});*/
				});
			});
			file_upload = true;
			console.log("NAME: " + name);
		}else{
			res.send('Image must be png, jpeg, jclient, gif or svg');
			return;
		}
	}
	if(file_upload){
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('UPDATE "user" SET first_name = $1, last_name = $2, email_id = $3, img_id = $4 WHERE user_id = $5', [fn, ln, emid, name, req.session.user.user_id], function(err, results){
				if(err) throw err;
			});
		});
	}
	else{
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('UPDATE "user" SET first_name = $1, last_name = $2, email_id = $3 WHERE user_id = $4', [fn, ln, emid, req.session.user.user_id], function(err, results){
				if(err) throw err;
			});
		});
	}
	res.redirect('/user/profile/');
};

exports.update_mks = function(req, res){
	var aid = req.params.a_id;
	var uid = req.body.user_id;
	var mks = req.body.mks;
	pg.connect(conString, function(err, client){
		if(err) throw err;
		client.query("SELECT * FROM `assignments` WHERE `id` = $1", [aid], function(err, rows, fields){
			if(err) throw err;
			if(rows.length != 1) res.send("0");
			console.log(rows);
			if(mks && mks != "" && mks.trim() != "" && isNaN(mks) == false && mks <= parseInt(rows[0].total_marks)){
				connection.query("UPDATE `submissions` SET `marks` = $1 WHERE `assignment_id` = $2 AND `user_id` = $3", [mks, aid, uid], function(err, rows, fields){if(err) throw err; res.send("1");});
			}else res.send("0");
		});
	});
}
exports.extraoptions = function(req, res){
	var course_id = req.params.course_id;
	var portal = req.params.portal;
	var option = req.params.option;
	if(option == "create" && portal == "assignments"){
		if(req.coursedet.role != 1){
			res.render('permission');
		}else{
			res.render("create_assignment", {notif: req.notifications, course_data: req.session.courses, me: req.session.user, role: 1, loc: req.coursedet, portal: "assignments"});
		}
	}
	else if(option == "delete" && portal == "assignments")
	{
		if(req.coursedet.role != 1) res.send("-1");
		else{
			var id = req.body.id;
			if(!id || id == "" || parseInt(id) == Nan || id < 0) res.send("-1");
			pg.connect(conString, function(err, client){
				if(err) throw err;
				client.query("DELETE FROM `assignments` WHERE `id` = $1", [id], function(err, rows, fields){
					if(err) throw err;
					connection.query("DELETE FROM `a_comments` WHERE `assignment_id` = $1", [id], function(err, rows, fields){
						if(err) throw err;
						connection.query("DELETE FROM `submissions` WHERE `assignment_id` = $1", [id], function(err, rows, fields){
							if(err) throw err;
							res.send("0");
						});
					});
				});
			});
		}
	}
	else if(option == 'details' && portal == 'assignments')
	{
		var id = req.body.id;
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('SELECT * FROM assignments WHERE id = $1', [id], function(err, result){
				if(err) throw err;
				if(result.rows[0])
					res.send(JSON.stringify(result.rows[0]));
				else
					res.send(0);
			});
		});
	}
	else if(option == 'file_upload' && portal == 'resources')
	{
		//TODO check file type for security!

		//-----upload file------------
		var file = req.files.upload_file || '';
		var file_expln = req.body.upload_file_expln;
		//------embed video------------
		var vid = req.body.embed_video;
		var vid_expln = req.body.embed_video_expln;
		//-------add link-------------
		var link_name = req.body.add_link;
		var link_url = req.body.add_link_url;
		var link_expln = req.body.add_link_expln;

		if(file.filename && file.size && file.name){
			//user wants to upload a file
			var fs = require('fs');
			var tmp_path = file.path;
			var target_path = './public/files/' + file.name;
			fs.rename(tmp_path, target_path, function(err){if(err) throw err;});
			pg.connect(conString, function(err, client){
				if(err) throw err;
				client.query('INSERT INTO resources (course_id, upload_date, filename, explanation, filetype, user_id) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id', [req.session.current_course, new Date().getTime() / 1000, file.name, file_expln, file.type, req.session.user.user_id], function(err, result){
					if(err) throw err;
					addNotification('RESOURCE', req.params.course_id, req.session.user.user_id, new Date().getTime() / 1000, result.rows[0].id);
				});
			});
		}

		if(vid){
			//user wants to embedded a video
			pg.connect(conString, function(err, client){
				if(err) throw err;
				client.query('INSERT INTO resource_links (course_id, upload_date, link_name, explanation, link_url, user_id, link_type) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING link_id', [req.session.current_course, new Date().getTime() / 1000, '_', vid_expln, vid, req.session.user.user_id, 'VIDEO_EMBED'], function(err, result){
					if(err) throw err;
					addNotification('RESOURCE', req.params.course_id, req.session.user.user_id, new Date().getTime() / 1000, result.rows[0].link_id);
				});
			});
		}

		if(link_url){
			//user wants to add a link
			pg.connect(conString, function(err, client){
				if(err) throw err;
				client.query('INSERT INTO resource_links (course_id, upload_date, link_name, explanation, link_url, user_id, link_type) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING link_id', [req.session.current_course, new Date().getTime() / 1000, link_name, link_expln, link_url, req.session.user.user_id, 'HYPERLINK'], function(err, result){
					if(err) throw err;
					addNotification('RESOURCE', req.params.course_id, req.session.user.user_id, new Date().getTime() / 1000, result.rows[0].link_id);

				});
			});
		}
		res.redirect('/courses/' + req.params.course_id + '/resources/');
	}
	else if(option == 'assignment_submission' && portal == 'assignments')
	{
		var a_id = req.body.assignment_id;
		var new_name = req.body.new_name;
		new_name = new_name || '';
		var fs = require('fs');
		var file = req.files.submission;
		if(!file.size || !file.name || !file.filename){
			res.redirect('/courses/' + req.params.course_id + '/assignments/');
		}
		else{
			var tmp_path = file.path;
			var fileid = genId(15);
			var date = new Date().getTime() / 1000;
			var name = '';
			var target_path = './public/submissions/' + fileid;console.log(target_path);
			if(!new_name) name = file.name;
			else name = new_name;
			fs.rename(tmp_path, target_path, function(err){if(err) throw err;});
			pg.connect(conString, function(err, client){
				if(err) throw err;
				client.query('INSERT INTO submissions (submission_id, assignment_id, submission_date, user_id, filename) VALUES ($1, $2, $3, $4, $5)', [fileid, a_id, date, req.session.user.user_id, name], function(err, result){
					if(err) throw err;
					res.redirect('/courses/' + req.params.course_id + '/assignments/');
				});
			});
		}
	}
	else res.redirect("/courses/" + req.params.course_id + "/main/");
}

exports.searchpage = function(req, res){
	var qu = req.query['q'];
	var course_results = '';
	var cq = "SELECT * FROM courses WHERE course_name ~* '[[:<:]]" + qu + "' LIMIT 50";
	var uq = 'SELECT * FROM "user" WHERE first_name ~* \'[[:<:]]' + qu + '\' OR last_name ~* \'[[:<:]]' + qu + '\' LIMIT 50';
	pg.connect(conString, function(err, client){
		if(err) throw err;
		client.query(cq, function(err, result){
			if(err) throw err;
			course_results = result.rows;
			client.query(uq, function(err, ures){
				if(err) throw err;
				res.render('searchpage', {me: req.session.user, notif: req.notifications, query: qu, course_data: req.session.courses, qcourse: course_results, quser: ures.rows});
			});
		});
	});
}

exports.notif = function(req, res){
	var tok = req.body.ids;
	if(tok && tok.length > 0){
		var query = 'UPDATE notif_view SET seen = 1 WHERE user_id = ' + req.session.user.user_id + ' AND (notif_id = ' + req.body.ids[0];
		for(var i = 1; i < tok.length; i++)
			query += ' OR notif_id = ' + tok[i];
		query += ')';
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query(query, function(err, result){
				if(err) throw err;
			});
		});
		res.send("1");
	}else res.send("0");
}

exports.person_interac = function(req, res){
	var cid = req.params.course_id;
	var pid = req.params.person_id;
	if(req.coursedet.role != 1){
		res.render('permission');
	}
	else{
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('SELECT * FROM "user" INNER JOIN user_course ON "user".user_id = user_course.user_id WHERE "user".user_id = $1 AND course_id = $2 AND role = 0', [pid, cid], function(err, result){
				if(err) throw err;
				if(!result.rows){
					res.send('An error occurred! The specified student is not registered for this course!');
				}
				else{
					client.query('select id, course_id, assignment_title, assignment_content, to_char(to_timestamp(start_date), \'HH12:MM am D,mon YYYY\') as start_date, to_char(to_timestamp(end_date), \'HH12:MM am D,mon YYYY\') as end_date, total_marks, submission_id, assignment_id, to_char(to_timestamp(submission_date), \'HH12:MM am D,mon YYYY\') as submission_date, user_id, filename, marks from assignments left join submissions on assignments.id = submissions.assignment_id and user_id = $1 where course_id = $2', [pid, cid], function(err, det){
						res.render('person_interac', {me: req.session.user, notif: req.notifications, course_data: req.session.courses, user: result.rows[0], contrib: det.rows, loc: req.coursedet, portal: 'people', role: 1});
					});
				}
			});
		});
	}
}

exports.generate_id = function(req, res){
	var id = genSpecialId(6);
	req.session.ckey = id;
	res.send(id);
}

exports.joincourse = function(req, res){
	var ckey = req.body.key;
	var query = 'SELECT * FROM user_course INNER JOIN courses ON courses.course_id = user_course.course_id WHERE user_id = ' + req.session.user.user_id + ' AND course_key = ' + ckey;
	pg.connect(conString, function(err, client){
		if(err) throw err;
		client.query('SELECT * FROM user_course INNER JOIN courses ON courses.course_id = user_course.course_id WHERE user_id = $1 AND course_key = $2', [req.session.user.user_id, ckey], function(err, result){
			if(err) throw err;
			if(result.rows.length){res.send('-1'); return;}//already a member of the course
			client.query('SELECT * FROM courses WHERE course_key = $1', [ckey], function(err, result1){
				if(err) throw err;
				if(!result1.rows.length){res.send('0'); return;} //no course with this key
				else{
					var id = result1.rows[0].course_key;
					req.session.courses.push(result.rows[0]);
					client.query('INSERT INTO user_course (user_id, course_id, role) VALUES ($1, $2, 0)', [req.session.user.user_id, result.rows[0].course_id, 1], function(err, result2){if(err) throw err; res.send(JSON.stringify(result1.rows[0])); return;});
				}
			});
		});
	});
}

exports.course_edit = function(req, res){
	if(req.coursedet.role != 1){
		res.render('permission');
		return;
	}
	var cid = req.params.course_id;
	var cname = req.body.cname;
	var clab = req.body.clab;
	var bg = req.files.masthead_img;
	var ckey = req.body.ckey;
	var file_upload = false;
	var name = '';
	if(ckey != req.session.ckey && ckey != req.coursedet.course_key){
		res.send('the course key does not match the key we sent you!');
		return;
	}
	if(bg.size && bg.filename && bg.name){
		var tmp_path = bg.path;
		var id = genId(15);
		var ext = bg.type;
		var type = '';
		switch(ext){
			case 'image/png':
				type = 'png';
				break;
			case 'image/jpeg':
				type = 'jclient';
				break;
			case 'image/gif':
				type = 'gif';
				break;
			case 'image/svg':
				type = 'svg';
				break;
		}
		if(type != ''){
			var tmp_path = bg.path;
			var id = genId(15);
			var fs = require('fs');
			var target_path = './public/images/masthead/' + id + '.' + type;console.log(target_path);
			fs.rename(tmp_path, target_path, function(err){if(err) throw err;});
			name = id + '.' + type;
			file_upload = true;
		}
		else{
			res.send('only svg, png, jclient, jpeg, gif images allowed!');
			return;
		}
	}
	if(file_upload){
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('UPDATE courses SET course_label = $1, course_name = $2, masthead_img = $3, course_key = $4 WHERE course_id = $5', [clab, cname, name, ckey, cid], function(err, result){if(err) throw err; });
		});
	}else{
		pg.connect(conString, function(err, client){
			if(err) throw err;
			client.query('UPDATE courses SET course_label = $1, course_name = $2, course_key = $3 WHERE course_id = $4', [clab, cname, ckey, cid], function(err, result){if(err) throw err; });
		});
	}
	res.redirect('/courses/' + cid + '/admin');
}
