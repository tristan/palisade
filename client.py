from functools import wraps
from flask import session, request, redirect, url_for, g
from palisade.rest import abort
import urllib3
import simplejson

# TODO: make this a config option
AUTH_SESSION_KEY = 'auth_session_cookie'

def require_login(redirect_endpoint):
    def d0(fn):
        @wraps(fn)
        def d1(*args, **kwargs):
            if session.get(AUTH_SESSION_KEY) is None:
                return redirect(url_for(redirect_endpoint, next=request.url))
            return fn(*args, **kwargs)
        return d1
    return d0

# TODO: make this a config option
BASE_URL = 'http://127.0.0.1:5001/api'
def init_login(provider, callback_endpoint):
    next = request.args.get('next') or request.referrer
    callback = url_for(callback_endpoint, provider=provider, next=next, _external=True)
    r = urllib3.PoolManager().request(
        'GET', 
        '{0}/login/{1}/init/?oauth_callback={2}'.format(BASE_URL, provider, callback))
    json = simplejson.loads(r.data)
    if 'redirect' not in json:
        abort(400, error=json.get('error', "didn't get redirect url from server"))
    cookies = r.getheader('set-cookie')
    session[AUTH_SESSION_KEY + '0'] = cookies
    return redirect(json['redirect'])

def verify_login(provider):
    cookies = session.pop(AUTH_SESSION_KEY + '0', None)
    if cookies is None:
        abort(400, message="no session set")
    headers = {'cookie': cookies}
    r = urllib3.PoolManager().request(
        'GET', 
        '{0}/login/{1}/verify/?{2}'.format(BASE_URL, provider, request.query_string),
        headers=headers)
    json = simplejson.loads(r.data)
    if 'error' in json:
        abort(400, error=json['error'])
    cookies = r.getheader('set-cookie', cookies)
    session[AUTH_SESSION_KEY] = cookies
    return json
