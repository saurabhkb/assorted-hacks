from flask import Flask, render_template, request, jsonify, redirect, abort
import time
from pymongo import MongoClient
import json

app = Flask(__name__)
client = MongoClient()
db = client['cloud']
v = db['vm']

@app.route('/')
def home():
	return render_template("index.html")

@app.route('/about')
def about():
	return render_template("about.html")

@app.route('/contact')
def contact():
	return render_template("contact.html")

@app.route('/provider/<p>')
def provider(p):
	if p == "Amazon":
		return redirect("http://aws.amazon.com/")
	elif p == "Azure":
		return redirect("http://azure.microsoft.com/en-us/")
	else:
		return abort(404)

@app.route('/fetch_results', methods = ['POST', 'GET'])
def fetch():
	#page_num = int(request.form['page'])
	#assert page_num > 0

	cores_min = int(request.form['cores_min'])
	cores_max = int(request.form['cores_max'])

	disk_min = int(request.form['disk_min']) * 10 ** 6
	disk_max = int(request.form['disk_max']) * 10 ** 6

	memory_min = int(request.form['memory_min']) * 10 ** 3
	memory_max = int(request.form['memory_max']) * 10 ** 3

	ssd_min = int(request.form['ssd_min']) * 10 ** 6
	ssd_max = int(request.form['ssd_max']) * 10 ** 6

	q = {
		"cores": {
			"$gte": cores_min,
			"$lte": cores_max
		},
		"ramMB": {
			"$gte": memory_min,
			"$lte": memory_max
		},
		"diskMB": {
			"$gte": disk_min,
			"$lte": disk_max
		},
		"flashMB": {
			"$gte": ssd_min,
			"$lte": ssd_max
		}
	}
	result = list(v.find(q, {'_id': False}))
	for r in result:
		r['provider'] = "<a target='_blank' href='/provider/%s'>%s</a>" % (r['provider'], r['provider'])
		r['ramGB'] = r['ramMB'] / 1000.0
		r['diskGB'] = r['diskMB'] / 1000.0
		r['flashGB'] = r['flashMB'] / 1000.0

		del r['ramMB']
		del r['diskMB']
		del r['flashMB']
	#return jsonify(length = len(result), result = result[page_num : page_num + 10])
	time.sleep(2)
	return jsonify(length = len(result), result = result)

app.run(debug = True)
