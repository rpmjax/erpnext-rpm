"""Local PoC HTTP test; credential files supplied separately, never committed."""
import json
from pathlib import Path
import requests

base = 'http://frontend:8080'
sessions = []
try:
    for filename, scope in [('pilot-login-credentials.json', 'Self'),
                            ('manager-login-credentials.json', 'Team')]:
        credential = json.loads(Path('/tmp', filename).read_text(encoding='utf-8-sig'))[0]
        session = requests.Session()
        sessions.append(session)
        assert session.post(base + '/api/method/login', data={
            'usr': credential['email'], 'pwd': credential['password']}).status_code == 200
        endpoint = base + '/api/method/rpm_worklog.reports.'
        response = session.get(endpoint + 'search_employees', params={'scope': scope})
        assert response.status_code == 200
        candidates = response.json()['message']['employees']
        assert candidates
        chosen = candidates[0]
        number = chosen['label'].split(' | ')[0]
        found = session.get(endpoint + 'search_employees', params={'scope': scope, 'text': number})
        assert chosen in found.json()['message']['employees']
        options = session.get(endpoint + 'options').json()['message']
        args = dict(report=options['reports'][0]['name'], scope=scope,
                    from_date='2026-09-01', to_date='2026-09-30', employee=chosen['value'])
        result = session.get(endpoint + 'run', params=args)
        assert result.status_code == 200
        assert result.json()['message']['employee_label'] == chosen['label']
        args['employee'] = 'does-not-exist'
        assert session.get(endpoint + 'run', params=args).status_code == 403
        if scope == 'Self':
            assert session.get(endpoint + 'search_employees', params={'scope': 'Team'}).status_code == 403
    assert requests.get(base + '/api/method/rpm_worklog.reports.search_employees').status_code in (401, 403)
    print('EMPLOYEE_FILTER_HTTP_PASS: authenticated search/filter, labels, forged ID and scope/Guest denial')
finally:
    for session in sessions:
        session.get(base + '/api/method/logout')
