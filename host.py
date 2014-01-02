from flask import Flask, render_template, redirect, url_for, send_file, request, jsonify
import pusher
from datastore import Datastore
import hashlib
import random, time
import traceback

PUSHER_KEY = '754be4ab2d0de2d2272b'
PUSHER_SECRET = '045de7c8b9e1f36548ac'
HOSPITAL_COLLECTION = 'hosp'

app = Flask(__name__)
p = pusher.Pusher(app_id = '60514', key = PUSHER_KEY, secret = PUSHER_SECRET)
d = Datastore()

@app.route('/')
def root():
	hosps = list(d.find(HOSPITAL_COLLECTION))
	return render_template("index.html", hospitals = hosps)

@app.route('/update', methods = ['POST'])
def update():
	try:
		hospital_id = int(request.form['hospital_id'])
		change = int(request.form['change'])
		orig = d.find_one(HOSPITAL_COLLECTION, {'hospital_id': hospital_id})
		assert orig['num_beds'] + change >= 0
		ret = d.update(HOSPITAL_COLLECTION, {'hospital_id': hospital_id}, {"$inc": {"num_beds": change}}, {'upsert': True})
		assert ret['ok'] == 1.0
		p['alert_channel'].trigger('status_update', {'bed_change': orig['num_beds'] + change, 'hospital_id': hospital_id})
		return jsonify(status = 'OK')
	except Exception as e:
		traceback.print_exc()
		return jsonify(status = 'ERROR')

@app.route('/hosp/<int:hosp_id>')
def hosp(hosp_id):
	hosp = d.find_one(HOSPITAL_COLLECTION, {'hospital_id': hosp_id})
	try:
		return render_template("hospital.html", hospital_id = hosp_id, hospital_name = hosp['hospital_name'], num_beds = hosp['num_beds'])
	except Exception as e:
		traceback.print_exc()
		return "error"

@app.route('/admin')
def admin():
	return render_template("admin.html")

@app.route('/add_hospital', methods = ['POST'])
def add():
	try:
		pwd = request.form['password']
		assert pwd == "fs8548e99f5f71365Ea63OI5934"
		hosp_name = request.form['hospital_name']
		num_beds = int(request.form['num_beds'])
		hosp_id = int(random.random() * time.time())
		d.insert(HOSPITAL_COLLECTION, {'hospital_name': hosp_name, 'hospital_id': hosp_id, 'num_beds': num_beds})
		return jsonify(status = "OK", hospital_id = hosp_id)
	except Exception as e:
		traceback.print_exc()
		return "invalid password"

@app.route('/view_hospitals', methods = ['POST'])
def view_hosp():
	try:
		pwd = request.form['password']
		assert pwd == "fs8548e99f5f71365Ea63OI5934"
		hosps = list(d.find(HOSPITAL_COLLECTION, fields = {'hospital_name': True, 'hospital_id': True, '_id': False}))
		return jsonify(hospitals = hosps)
	except Exception as e:
		traceback.print_exc()
		return "invalid password"

@app.route('/del_hospital', methods = ['POST'])
def del_hosp():
	try:
		pwd = request.form['password']
		assert pwd == "fs8548e99f5f71365Ea63OI5934"
		hospital_id = int(request.form['hospital_id'])
		d.remove(HOSPITAL_COLLECTION, {'hospital_id': hospital_id})
		return jsonify(status = "OK")
	except Exception as e:
		traceback.print_exc()
		return "invalid password or hospital id"


@app.errorhandler(404)
def page_not_found(e):
	return render_template("404.html"), 404

app.run(debug = True)
