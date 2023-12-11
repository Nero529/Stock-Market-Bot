from flask import Flask
from threading import Thread

app = Flask('')


@app.route('/')
def home():
  return ('Still running')


def run():
  try:
    app.run(host='0.0.0.0', port=8080)
  except:
    pass


def run_code():
  try:
    t = Thread(target=run)
    t.start()
  except:
    pass
