from flask import Flask, render_template, redirect, url_for, send_file, request, jsonify
import pusher
from datastore import Datastore

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
		print e
		return jsonify(status = 'ERROR')

@app.route('/hosp/<int:hosp_id>')
def hosp(hosp_id):
	hosp = d.find_one(HOSPITAL_COLLECTION, {'hospital_id': hosp_id})
	try:
		return render_template("hospital.html", hospital_id = hosp_id, hospital_name = hosp['hospital_name'], num_beds = hosp['num_beds'])
	except Exception as e:
		return "error"

@app.errorhandler(404)
def page_not_found(e):
	return render_template("404.html"), 404

app.run(debug = True)
