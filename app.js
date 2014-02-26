
/**
 * Module dependencies.
 */

var express = require('express')
	, routes = require('./routes')
	, MemoryStore = express.session.MemoryStore
	, sessionStore = new MemoryStore();

var app = module.exports = express.createServer();
pg = require('pg');
conString = "pg://postgres:saurabh@localhost/finance";
// Configuration

app.configure(function(){
	app.set('views', __dirname + '/views');
	app.set('view engine', 'jade');
	app.set('view options', {layout: false});
	app.use(express.bodyParser());
	app.use(express.methodOverride());
	app.use(express.cookieParser());
	app.use(express.session({store: sessionStore, secret: "ssfkdsjlf", key: "express.sid"}));
	app.use(app.router);
	app.use(express.static(__dirname + '/public'));
});

app.configure('development', function(){
	app.use(express.errorHandler({ dumpExceptions: true, showStack: true }));
});

app.configure('production', function(){
	app.use(express.errorHandler());
});

//Middleware
function userAuth(req, res, next) {
	res.header('Cache-Control', 'no-cache, private, no-store, must-revalidate, max-stale=0, post-check=0, pre-check=0');
	if(req.session.is_logged_in == true)
		next();
	else
		res.redirect('/');
}

// Routes

app.get('/', routes.index);
app.post('/signin', routes.signin);
app.get('/forgot_password', routes.forgot_pwd);
app.post('/sec_ques', routes.secques);
app.post('/forgot_pwd_user', routes.forgot_pwd_user);
app.get('/signup', routes.signup);
app.post('/create_user', routes.create_user);
app.get('/signout', userAuth, routes.signout);
app.get('/profile', userAuth, routes.profile);
app.post('/edit_profile', userAuth, routes.edit_profile);
app.get('/home', userAuth, routes.home);
app.get('/search', userAuth, routes.search);
app.get('/company/:company_name', userAuth, routes.company);
app.get('/company/:company_name/bond', userAuth, routes.bond);
app.get('/company/:company_name/history', userAuth, routes.history);
app.post('/purchase_stock', userAuth, routes.purchase_stock);
app.post('/purchase_bonds', userAuth, routes.purchase_bonds);
app.get('/sell_stock', userAuth, routes.sell_stock);
app.post('/sell_transaction', userAuth, routes.sell_transaction);

app.listen(3000, function(){
	console.log("Express server listening on port %d in %s mode", app.address().port, app.settings.env);
})
