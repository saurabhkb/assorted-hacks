var mysql = require('mysql');
var conString = {host: 'localhost', user: 'root', password: 'saurabh', database: 'finance'};
/*
 * GET home page.
 */


exports.index = function(req, res){
	res.render('index');
};

exports.signin = function(req, res){
	var emid = req.body.user.email_id;
	var pwd = req.body.user.password;
	var conn = mysql.createConnection(conString);
	conn.connect();
	conn.query('SELECT * FROM users WHERE emailid = ? AND passwd = ?', [emid, pwd], function(err, result) {
		if(err) throw err;
		conn.end();
		if(result.length == 1) {
			req.session.is_logged_in = true;
			req.session.user = result[0];
			console.log(req.session.user);
			res.redirect('/home');
		}
		else {
			res.redirect('/');
		}
	});
}

exports.forgot_pwd = function(req, res) {
	res.render('forgot_password');
}
exports.secques = function(req, res) {
	var emid = req.body.emid;
	var conn = mysql.createConnection(conString);
	conn.connect();
	conn.query('SELECT security_question FROM users WHERE emailid = ?', [emid], function(err, result) {
		if(err) throw err;
		if(result.length == 0) {
			res.send("0");
			return;
		}
		else if(result[0]['security_question'] == null) {
			res.send("1");
			return;
		}
		else {
			res.send(result[0]['security_question']);
			return;
		}
	});
}
exports.forgot_pwd_user = function(req, res) {
	var emid = req.body.emailid;
	var sa = req.body.sa;
	var conn = mysql.createConnection(conString);
	conn.connect();
	conn.query('SELECT * FROM users WHERE emailid = ? AND security_ans = ?', [emid, sa], function(err, result) {
		if(err) throw err;
		console.log(result);
		if(result.length == 0) {
			res.send("incorrect answer!");
			return;
		}
		else {
			req.session.is_logged_in = true;
			req.session.user = result[0];
			console.log(req.session.user);
			res.redirect('/home');
		}
	});
}
exports.signup = function(req, res) {
	res.render('signup');
}

exports.create_user = function(req, res) {
	var user = req.body.user;
	var conn = mysql.createConnection(conString);
	conn.connect();
	//data verification

	var email_r = new RegExp("^[a-zA-Z0-9_\+-]+(\.[a-zA-Z0-9_\+-]+)*@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.([a-zA-Z]{2,4})$");
	var pno_r = new RegExp("^[2-9]{2}[0-9]{8}$");
	var name_r = new RegExp("^[a-zA-Z\']+$");
	var pwd_r = new RegExp("^[a-zA-Z0-9_-]{6,18}$");

	console.log(email_r.test(user.emid) + ", " + pno_r.test(user.pno) + ", " + name_r.test(user.fn) + ", " + name_r.test(user.mn) + ", " +  name_r.test(user.ln) + ", " + pwd_r.test(user.pwd));


	if(email_r.test(user.emid) && pno_r.test(user.pno) && name_r.test(user.fn) && name_r.test(user.mn) && name_r.test(user.ln) && pwd_r.test(user.pwd)) {
		conn.query("SELECT * FROM users WHERE emailid = ?", [user.emid], function(err, result) {
			if(err) throw err;
			if(result.length != 0)
				res.send("a user with that email id already exists!");
			else
				conn.query("INSERT INTO users (first_name, middle_name, last_name, emailid, passwd, cell_no, account_no) VALUES (?, ?, ?, ?, ?, ?, ?)", [user.fn, user.mn, user.ln, user.emid, user.pwd, user.pno, user.accno], function(err, result) {
					if(err) throw err;
					req.session.is_logged_in = true;
					conn.query("INSERT INTO account_details (account_no, balance) VALUES (?, ?)", [user.accno, 1000], function(err, result) {
						req.session.user = {emailid: user.emid, passwd: user.pwd, first_name: user.fn, last_name: user.ln, middle_name: user.mn, account_no: user.accno, cell_no: user.pno};
						res.redirect('/home');
					});
				});
		});
	}
	else res.redirect('/signup');
}

exports.profile = function(req, res) {
	var conn = mysql.createConnection({host: 'localhost', user: 'root', password: 'saurabh', database: 'finance'});
	conn.connect();
	var emid = req.session.user.emailid;
	conn.query('SELECT account_details.*, emailid, passwd, first_name, last_name, middle_name, cell_no, security_question, security_ans, DATE_FORMAT(last_login, "%a %d %b %Y") as last_login FROM users NATURAL JOIN account_details WHERE emailid = ?', [emid], function(err, result) {
		res.render('profile', {user: result[0]});
	});
}




exports.home = function(req, res) {
	var conn = mysql.createConnection({host: 'localhost', user: 'root', password: 'saurabh', database: 'finance'});
	conn.connect();
	var emid = req.session.user.emailid;
	conn.query(
		"SELECT DISTINCT(emailid), name, SUM(case when transaction_type = 0 then number_trs when transaction_type = 1 then -number_trs end) as num_bought, stock.*, ((day_high - day_low) / day_low) * 100 as day_change, SUM(case when transaction_type = 0 then number_trs when transaction_type = 1 then -number_trs end) * last_trade_price as total FROM stock_transaction NATURAL JOIN stock NATURAL JOIN stock_offering WHERE emailid = ? group by symbol, type",
		[emid],
		function(err, stockresult) {
			conn.query(
				"SELECT DISTINCT(emailid), name, SUM(number_trs) as tot_number, SUM(number_trs) * price as total, bond.symbol, bond.type, bond.principal, bond.yield, bond.coupon, bond.maturity, bond.price, DATE_FORMAT(bond.offer_date, '%Y-%c-%d') as offer_date FROM bond_transaction NATURAL JOIN bond NATURAL JOIN bond_offering WHERE emailid = ? AND transaction_type = 0 group by symbol, type, offer_date",
				[emid],
				function(err, bondresult) {
					if(err) throw err;
					res.render('home', {s:stockresult, b: bondresult});
				}
			);
		}
	);
}

exports.sell_stock = function(req, res) {
	var conn = mysql.createConnection({host: 'localhost', user: 'root', password: 'saurabh', database: 'finance'});
	conn.connect();
	var emid = req.session.user.emailid;
	conn.query("SELECT symbol, type, last_trade_price, SUM(case when transaction_type = 0 then number_trs when transaction_type = 1 then -number_trs end) as tot_number FROM users NATURAL JOIN stock_transaction NATURAL JOIN stock where emailid = ? group by symbol, type", [emid], function(err, result) {
		if(err) throw err;
		res.render('sell_stock', {d: result});
	});
}

exports.sell_transaction = function(req, res) {
	var conn = mysql.createConnection({host: 'localhost', user: 'root', password: 'saurabh', database: 'finance'});
	conn.connect();
	var emid = req.session.user.emailid;
	var num = req.body.num;
	var symb = req.body.symbol;
	var type = req.body.type;
	var t = new Date();
	var month = t.getMonth() + 1;
	var date = t.getFullYear() + "-" + month + "-" + t.getDate();
	conn.query("insert into stock_transaction (emailid, number_trs, symbol, type, date, transaction_type) values (?, ?, ?, ?, ?, ?)", [emid, num, symb, type, date, 1], function(err, result) {
		if(err) throw err;
		conn.query("UPDATE users NATURAL JOIN account_details SET balance = balance + (select last_trade_price from stock where symbol = ? and type = ?) * ? WHERE emailid = ?", [symb, type, num, emid], function(err, result) {
			if(err) throw err;
			res.send("1");
			return;
		});
	});
}

exports.purchase_stock = function(req, res) {
	var symbol = req.body.symbol;
	var number = req.body.num;
	var type = req.body.type;
	if(!number || !isFinite(number) || number <= 0) {
		res.send("-3");
		return;
	}
	var conn = mysql.createConnection({host: 'localhost', user: 'root', password: 'saurabh', database: 'finance'});
	conn.connect();
	var emid = req.session.user.emailid;
	conn.query("SELECT last_trade_price FROM stock WHERE symbol = ? and type = ?", [symbol, type], function(err, result) {
		if(err) throw err;
		if(!result.length || result.length > 1) {
			res.send("-1");
			return;
		} else {
			var rate = result[0]['last_trade_price'];
			conn.query("SELECT balance FROM users NATURAL JOIN account_details WHERE emailid = ?", [emid], function(err, result) {
				if(err) throw err;
				var cost = number * rate;
				if(!result.length || result.length > 1) {
					res.send("-1");
					return;
				} else if(result[0]['balance'] < cost) {
					res.send("-2");
					return;
				} else {
					var t = new Date();
					var month = t.getMonth() + 1;
					var date = t.getFullYear() + "-" + month + "-" + t.getDate();
					conn.query("UPDATE users NATURAL JOIN account_details SET balance = balance - ? WHERE emailid = ?", [cost, emid], function(err, result) {
						if(err) throw err;
						conn.query("INSERT INTO stock_transaction VALUES (?, ?, ?, ?, ?, ?)", [emid, number, symbol, type, date, 0], function(err, result) {
							if(err) throw err;
							res.send("0");
							});
					});
				}
			});
		}
	});
}

exports.purchase_bonds = function(req, res) {
	var symbol = req.body.symbol;
	var number = req.body.num;
	var type = req.body.type;
	var offer_date = req.body.offer_date;
	console.log(symbol + ", " + number + ", " + ", " + type + ", " + offer_date);
	if(!number || !isFinite(number) || number <= 0) {
		res.send("-3");
		return;
	}
	var conn = mysql.createConnection({host: 'localhost', user: 'root', password: 'saurabh', database: 'finance'});
	conn.connect();
	var emid = req.session.user.emailid;
	conn.query("SELECT price FROM bond WHERE symbol = ? and type = ? and DATE_FORMAT(offer_date, '%Y-%c-%d') = ?", [symbol, type, offer_date], function(err, result) {
		if(err) throw err;
		if(!result.length || result.length > 1) {
			res.send("-1");
			return;
		} else {
			var rate = result[0]['price'];
			conn.query("SELECT balance FROM users NATURAL JOIN account_details WHERE emailid = ?", [emid], function(err, result) {
				if(err) throw err;
				var cost = number * rate;
				if(!result.length || result.length > 1) {
					res.send("-1");
					return;
				} else if(result[0]['balance'] < cost) {
					res.send("-2");
					return;
				} else {
					var t = new Date();
					var month = t.getMonth() + 1;
					var date = t.getFullYear() + "-" + month + "-" + t.getDate();
					conn.query("UPDATE users NATURAL JOIN account_details SET balance = balance - ? WHERE emailid = ?", [cost, emid], function(err, result) {
						if(err) throw err;
						conn.query("INSERT INTO bond_transaction (emailid, symbol, type, number_trs, offer_date, date) VALUES (?, ?, ?, ?, ?, ?)", [emid, symbol, type, number, offer_date, date], function(err, result) {
								if(err) throw err;
								res.send("0");
							});
					});
				}
			});
		}
	});
}


exports.signout = function(req, res) {
	var t = new Date();
	var month = t.getMonth() + 1;
	var date = t.getFullYear() + "-" + month + "-" + t.getDate();
	var conn = mysql.createConnection({host: 'localhost', user: 'root', password: 'saurabh', database: 'finance'});
	conn.connect();
	var emid = req.session.user.emailid;
	conn.query('update users set last_login = ? where emailid = ?', [date, emid], function(err, result) {
		if(err) throw err;
		req.session.is_logged_in = false;
		req.session.user = null;
		res.redirect('/');
	});
}

exports.search = function(req, res) {
	var q = req.query["q"];
	var conn = mysql.createConnection({host: 'localhost', user: 'root', password: 'saurabh', database: 'finance'});
	conn.connect();
	var query = "SELECT * FROM company WHERE SOUNDEX(name) = SOUNDEX('" + q + "') OR name LIKE '" + q + "%'";
	conn.query(query,  function(err, result) {
		if(err) throw err;
		res.render('search', {r: result, q: q});
	});
}

exports.company = function(req, res) {
	var cname = req.params.company_name;
	var conn = mysql.createConnection({host: 'localhost', user: 'root', password: 'saurabh', database: 'finance'});
	conn.connect();
	conn.query('SELECT * FROM company NATURAL JOIN stock_offering NATURAL JOIN stock WHERE name = ?', [cname], function(err, result) {
		if(err) throw err;
		res.render('company', {c: result});
	});

}

exports.history = function(req, res) {
	var cname = req.params.company_name;
	var conn = mysql.createConnection({host: 'localhost', user: 'root', password: 'saurabh', database: 'finance'});
	conn.connect();
	conn.query('SELECT * FROM history WHERE name = ? ORDER BY year, month', [cname], function(err, result) {
		if(err) throw err;
		res.render('history', {h: result});
	});

}


exports.edit_profile = function(req, res) {
	var conn = mysql.createConnection({host: 'localhost', user: 'root', password: 'saurabh', database: 'finance'});
	conn.connect();
	var pno_r = new RegExp("^[2-9]{2}[0-9]{8}$");
	var name_r = new RegExp("^[a-zA-Z\']+$");
	if(req.body.type == 1 && pno_r.test(req.body.pno) && name_r.test(req.body.fn) && name_r.test(req.body.mn) && name_r.test(req.body.ln)) {
		conn.query('UPDATE users SET first_name = ?, last_name = ?, middle_name = ?, cell_no = ? WHERE emailid = ?', [req.body.fn, req.body.ln, req.body.mn, req.body.pno, req.session.user.emailid], function(err, result) {
			if(err) {throw err; res.send(null);}
			res.send("1");
		});
	}else if(req.body.type == 2 && req.body.sq && req.body.sq.trim() && req.body.sa && req.body.sa.trim()) {
		conn.query('UPDATE users SET security_question = ?, security_ans = ? WHERE emailid = ?', [req.body.sq, req.body.sa, req.session.user.emailid], function(err, result) {
			if(err) {throw err; res.send(null);}
			res.send("1");
		});
	}else res.send(null);
}

exports.bond = function(req, res) {
	var cname = req.params.company_name;
	var conn = mysql.createConnection({host: 'localhost', user: 'root', password: 'saurabh', database: 'finance'});
	conn.connect();
	conn.query('SELECT company.*, bond_offering.symbol, bond.type, bond.principal, bond.yield, bond.coupon, bond.maturity, bond.price, DATE_FORMAT(bond.offer_date, "%Y-%c-%d") as offer_date FROM company NATURAL JOIN bond_offering NATURAL JOIN bond WHERE name = ?', [cname], function(err, result) {
		if(err) throw err;
		console.log(result);
		res.render('bond', {c: result});
	});
}
