var express = require('express');
var stylus = require("stylus");
var nib = require("nib");
var app = express.createServer(express.logger());
MemoryStore = express.session.MemoryStore;
var sessionStore = new MemoryStore();
app.configure(function(){
app.use(stylus.middleware({
                src: __dirname + '/public',
                compile: function(str, path){
                                return stylus(str).set('filename', path).set('compress', true).use(nib());
                        }
        }));
        app.set('views', __dirname + '/views');
        app.set('view engine', 'jade');
        app.set('view options', {layout: false});
        app.use(express.bodyParser({keepExtensions: true, uploadDir: __dirname + '/public/uploads'}));
        app.use(express.cookieParser());
        app.use(express.session({store: sessionStore, secret: "keyboard cat", key: "express.sid"}));
        app.use(express.methodOverride());
        app.use(app.router);
        app.use(express.static(__dirname + '/public'));
});

app.get('/', function(request, response) {
  response.render("index.jade", {title: "Teachfruit"});
  });

  var port = process.env.PORT || 5000;
  app.listen(port, function() {
    console.log("Listening on " + port);
    });
