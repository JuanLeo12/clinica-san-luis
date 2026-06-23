from app import app
c = app.test_client()
r = c.get('/api/state')
d = r.json
if 'error' in d:
    print('Error:', d['error'][:200])
else:
    print('Keys:', list(d.keys())[:8])
    if d.get('appointments'):
        apt = d['appointments'][0]
        print('First appointment keys:', list(apt.keys()))
        print('Patient:', apt.get('patient'))
        print('Specialty:', apt.get('specialty'))