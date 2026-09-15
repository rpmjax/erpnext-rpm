import json
import subprocess
import sys

# Pass normal docker compose flags (e.g. --env-file ... -f deploy/compose.yaml).
config = json.loads(subprocess.check_output(['docker','compose',*sys.argv[1:],'config','--format','json'],text=True))
assert config['services']['queue-short']['command'] == ['bench','worker','--queue','short,default']
assert config['services']['queue-long']['command'] == ['bench','worker','--queue','long']
print('COMPOSE_QUEUE_ARGUMENTS_PASS')
