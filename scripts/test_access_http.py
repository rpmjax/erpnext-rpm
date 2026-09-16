"""Read/denial probes using separately supplied local PoC credentials."""
import json
from pathlib import Path
import requests

base = 'http://frontend:8080'
for filename in ('pilot-login-credentials.json', 'manager-login-credentials.json'):
    credential = json.loads(Path('/tmp', filename).read_text(encoding='utf-8-sig'))[0]
    with requests.Session() as session:
        assert session.post(base+'/api/method/login', data={
            'usr':credential['email'], 'pwd':credential['password']}).status_code == 200
        try:
            assert session.get(base+'/api/method/rpm_worklog.access.users').status_code == 403
            assert session.post(base+'/api/method/rpm_worklog.access.enroll', data={
                'users':json.dumps([credential['email']]), 'mode':'manager'}).status_code == 403
            assert session.get(base+'/api/resource/RPM%20Work%20Log%20Access/RPM%20Work%20Log%20Access').status_code == 403
        finally:
            session.get(base+'/api/method/logout')
assert requests.get(base+'/api/method/rpm_worklog.access.users').status_code in (401,403)
print('ACCESS_HTTP_PASS: employee/manager page and endpoints denied; Guest denied')
