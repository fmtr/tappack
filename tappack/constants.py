from datetime import datetime

ENCODING = 'utf-8'
NAME_MANIFEST = 'manifest.yaml'
RUNTIME = datetime.now()
CODE_MASK_DEFAULT = '{{"download":tasmota.urlfetch("{url}"), "restart":tasmota.cmd("restart 1")}}'
