import multiprocessing


bind = '127.0.0.1:{{ gunicorn_port }}'
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 60
