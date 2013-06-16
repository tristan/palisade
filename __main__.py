"""
Run the user login service as it's own service
"""
import os, sys

def create_app(store):
    from flask import Flask
    app = Flask(__name__)
    app.config.from_object('palisade.settings')

    # Setup session storage
    from flaskext.kvsession import KVSessionExtension
    KVSessionExtension(store, app)

    import rest
    app.register_blueprint(rest.blueprint, url_prefix='/api')
    return app

# use failsafe tool when using bare flask
from flask_failsafe import failsafe
create_app_flask_dbg = failsafe(create_app)

app = None
sys.path.append(os.getcwd()) # TODO: why do i need this?
if 'SERVER_SOFTWARE' in os.environ:
    if os.environ['SERVER_SOFTWARE'].startswith('Dev'):
        DEBUG_MODE = True
    from simplekv.gae import NdbStore
    from google.appengine.ext import ndb
    class Session(ndb.Expando):
        pass
    store = NdbStore(Session)
    app = create_app(store)
else:
    from simplekv.memory import DictStore
    store = DictStore()
    app = create_app_flask_dbg(store)
    app.run(host='127.0.0.1',port=5001,debug=True)


