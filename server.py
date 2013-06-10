from flask import Flask
from flask import render_template
from flask import request
from Grapher import Grapher
import json
from unidecode import unidecode

app = Flask(__name__)
g = Grapher()

@app.route('/')
def root():
	return render_template('index.html')

@app.route('/relate', methods = ['GET'])
def relate():
	keyword = request.args.get('keyword')
	data = g.getRelatedNodes(keyword)
	keywords = []
	for elem in data:
		keywords.append(unidecode(elem[0]))
	return json.dumps({'keywords': keywords})

#app.run(debug = False)
