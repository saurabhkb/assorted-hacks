from flask import Flask, render_template, request, jsonify, redirect, abort
from pymongo import MongoClient
import json
import os

app = Flask(__name__)
client = MongoClient()
db = client['cloud']
v = db['vm']

providers = v.distinct('provider')
parametric_fields = [
			{'name': 'CPU Cores', 'class': 'cores', 'unit': 'cores', 'min': 1, 'max': 20, 'step': 1, 'show_start': 1, 'show_end': 20},
			{'name': 'Memory (GB)', 'class': 'ramGB', 'unit': 'GB', 'min': 0, 'max': 250, 'step': 5, 'show_start': 0, 'show_end': 80},
			{'name': 'Disk Space (GB)', 'class': 'diskGB', 'unit': 'GB', 'min': 0, 'max': 2500, 'step': 10, 'show_start': 0, 'show_end': 2000},
			{'name': 'SSD (GB)', 'class': 'flashGB', 'unit': 'GB', 'min': 0, 'max': 2500, 'step': 50, 'show_start': 0, 'show_end': 550},
		]
nonparametric_fields = [ {'name': 'Provider', 'class': 'provider'}, {'name': 'Region', 'class': 'region'}, {'name': 'Server Type', 'class': 'serverType'}, {'name': 'Upfront Cost ($)', 'class': 'upfrontCost'}, {'name': 'Hourly Cost ($)', 'class': 'hourlyCost'} ]

@app.route('/')
def home():
	return render_template("index.html", providers = providers, parametric_fields = parametric_fields, nonparametric_fields = nonparametric_fields)

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

	disk_min = int(j['diskGB_min']) * 10 ** 3
	disk_max = int(j['diskGB_max']) * 10 ** 3

	memory_min = int(j['ramGB_min']) * 10 ** 3
	memory_max = int(j['ramGB_max']) * 10 ** 3

	ssd_min = int(j['flashGB_min']) * 10 ** 3
	ssd_max = int(j['flashGB_max']) * 10 ** 3

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
