from flask import Flask, render_template, request, jsonify, redirect, abort
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
	elif p == "Rackspace":
		return redirect("http://www.rackspace.com/")
	elif p == "Google":
		return redirect("https://cloud.google.com/")
	elif p == "Linode":
		return redirect("https://www.linode.com/")
	else:
		return abort(404)

@app.route('/fetch_results', methods = ['POST', 'GET'])
def fetch():
	#TODO some kind of checking here
	j = request.get_json()

	cores_min = int(j['cores_min'])
	cores_max = int(j['cores_max'])

	disk_min = int(j['disk_min']) * 10 ** 3
	disk_max = int(j['disk_max']) * 10 ** 3

	memory_min = int(j['memory_min']) * 10 ** 3
	memory_max = int(j['memory_max']) * 10 ** 3

	ssd_min = int(j['ssd_min']) * 10 ** 6
	ssd_max = int(j['ssd_max']) * 10 ** 6

	providers = j['providers']

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
		},
		"$or": providers
	}
	try:
		result = list(v.find(q, {'_id': False}))
		for r in result:
			r['provider'] = "<a target='_blank' href='/provider/%s'>%s</a>" % (r['provider'], r['provider'])
			r['ramGB'] = r['ramMB'] / 1000.0
			r['diskGB'] = r['diskMB'] / 1000.0
			r['flashGB'] = r['flashMB'] / 1000.0

			del r['ramMB']
			del r['diskMB']
			del r['flashMB']
		return jsonify(length = len(result), result = result)
	except:
		return jsonify(length = 0, result = [])

app.run(debug = True)
