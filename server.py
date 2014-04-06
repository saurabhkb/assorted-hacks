from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import json

app = Flask(__name__)
client = MongoClient()
db = client['cloud']
v = db['vm']

@app.route('/')
def home():
	return render_template("index.html")

@app.route('/fetch_results', methods = ['POST', 'GET'])
def fetch():
	page_num = int(request.form['page'])
	assert page_num > 0

	cores_min = int(request.form['cores_min'])
	cores_max = int(request.form['cores_max'])

	disk_min = int(request.form['disk_min']) * 10 ** 6
	disk_max = int(request.form['disk_max']) * 10 ** 6

	memory_min = int(request.form['memory_min']) * 10 ** 3
	memory_max = int(request.form['memory_max']) * 10 ** 3

	ssd_min = int(request.form['ssd_min']) * 10 ** 6
	ssd_max = int(request.form['ssd_max']) * 10 ** 6

	q = {"cores": {"$gte": cores_min, "$lte": cores_max}, "ramMB": {"$gte": memory_min, "$lte": memory_max}, "diskMB": {"$gte": disk_min, "$lte": disk_max}, "flashMB": {"$gte": ssd_min, "$lte": ssd_max}}
	result = list(v.find(q, {'_id': False}))
	#return jsonify(length = len(result), result = result[page_num : page_num + 10])
	return jsonify(length = len(result), result = result)

app.run(debug = True)
