"""Check the actual deploy.sh serializer and optionally a live Bench parser.

python scripts/test_enroll_cli.py [CONTAINER SITE]
Live probe calls frappe._dict only; no user/role/site data changes.
"""
import ast
import json
from pathlib import Path
import re
import subprocess
import sys
from unittest.mock import patch

script = (Path(__file__).resolve().parents[1] / 'deploy/deploy.sh').read_text()
code = re.search(r"python -c '(.*?)' \"\$RPM_SITE\"", script).group(1)
for role in ('employee', 'manager'):
    user = "quote'\"\\line\n$(touch /tmp/should-not-exist)@example.invalid"
    with patch.object(sys, 'argv', ['-c', 'frontend', user, role]), patch.object(subprocess, 'run') as run:
        exec(compile(code, 'deploy.sh enroll serializer', 'exec'), {})
        argv = run.call_args.args[0]
        assert run.call_args.kwargs == {'check': True}
    expected = {'user': user, 'manager': role == 'manager'}
    assert argv[:6] == ['bench', '--site', 'frontend', 'execute', 'rpm_worklog.bootstrap.enroll', '--kwargs']
    assert ast.literal_eval(argv[6]) == expected
    if len(sys.argv) == 3:
        # Exercise the installed Bench eval/parser with the exact serialized kwargs.
        result = subprocess.check_output(['docker', 'exec', sys.argv[1], 'bench', '--site',
            sys.argv[2], 'execute', 'frappe._dict', '--kwargs', argv[6]], text=True)
        assert json.loads(result) == expected
print('ENROLL_CLI_PASS: employee/manager booleans and quoted input' +
      ('; live Bench parser passed' if len(sys.argv) == 3 else ''))
