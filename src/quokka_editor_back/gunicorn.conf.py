from quokka_editor_back.settings import LOGGING

workers = 2
keepali = 30
worker_class = "uvicorn.workers.UvicornWorker"
bind = ["0.0.0.0:8080"]

access_log = "-"
errorlog = "-"
loglevel = "info"
logconfig_dict = LOGGING

forwarded_allow_ips = "*"
