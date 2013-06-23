from functools import wraps
from flask import session, request, redirect as flask_redirect, url_for
from werkzeug.exceptions import HTTPException
from . import api

def require_login(logged_in_key, redirect_endpoint, **redirect_kwargs):
    def d0(fn):
        @wraps(fn)
        def d1(*args, **kwargs):
            if session.get(logged_in_key) is None:
                return flask_redirect(url_for(redirect_endpoint, **redirect_kwargs))
            return fn(*args, **kwargs)
        return d1
    return d0

def init_login(verify_endpoint, redirect=False, *args):
    def d0(fn):
        @wraps(fn)
        def d1(provider):
            # get any extra arguments on the query path
            _args = dict([(a, request.args[a]) for a in args if a in request.args])
            callback = url_for(verify_endpoint, provider=provider, _external=True, **_args)
            redirect_url = api.init_login(provider, callback)
            # abort should stop us from getting here if we won't have a 'redirect' key
            return fn(redirect_url)
        return d1
    # if redirect is True, then return an instance of the decorator
    # that automatically does the flask redirection
    if redirect:
        return d0(lambda url: flask_redirect(url))
    return d0

def verify_login(fn):
    @wraps(fn)
    def d1(provider):
        user = api.verify_login(provider, **request.args)
        # user should be an instance of .models.User
        return fn(user)
    return d1


def gen_rest_clients(SERVICE_BASE_URL='http://127.0.0.1:5000/api'):
    """Generates functions for accessing the init_login and verify_login functions via REST (using urllib3)
    (e.g. like one might use from a desktop application)

    SERVICE_BASE_URL: the base url of the remote service
    returns: a tuple of the auth functions (
        init_login(provider, callback_endpoint, **kwargs) : (redirect_url, session_cookie), 
        verfify_login(provider, query_string, session_cookie) : (user, session_cookie)
    )
    """
    import urllib3
    import simplejson
    def example_rest_init_login(provider, verify_url=None):
        """Initiates the login procedure
        provider: the oauth provider name (e.g. facebook)
        verify_url: the url the service should redirect to, if left as None the service will use
                    it's default which just returns a blank page
        returns: a tuple containing (
            the autorisation redirect url, 
            the session cookie to give to `verify_login()`
        )
        """
        r = urllib3.PoolManager().request(
            'GET', 
            '{0}/login/{1}/init/?oauth_callback={2}'.format(SERVICE_BASE_URL, provider, verify_url))
        json = simplejson.loads(r.data)
        if 'redirect' not in json:
            abort(400, error=json.get('error', "didn't get redirect url from server"))
        cookies = r.getheader('set-cookie')
        return (json['redirect'], cookies)

    def example_rest_verify_login(provider, query_string, session_cookie):
        """Verifies the authorisation and returns the user
        provider: the oauth provider name (e.g. facebook)
        query_string: a query string containing the `oauth_verifier` or `code` value returned by the provider
        session_cookie: the session cookie returned by `init_login()`

        returns a tuple containing (
            the user dict,
            the session key to use to make authorized calls to the REST API
        )
        """
        if session_cookie is None:
            abort(400, message="no session set")
        headers = {'cookie': session_cookie}
        r = urllib3.PoolManager().request(
            'GET', 
            '{0}/login/{1}/verify/?{2}'.format(BASE_URL, provider, query_string),
            headers=headers)
        json = simplejson.loads(r.data)
        if 'error' in json:
            abort(400, error=json['error'])
        cookies = r.getheader('set-cookie', cookies)
        return (json, session_cookie)

    return (example_rest_init_login, example_rest_verify_login)
