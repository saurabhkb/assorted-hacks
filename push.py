import pusher
import random

p = pusher.Pusher(app_id = '60514', key='754be4ab2d0de2d2272b', secret='045de7c8b9e1f36548ac')

p['test_channel1'].trigger('my_event', {'message': str(random.random()), 'author': 'Saurabh Bapat'})
