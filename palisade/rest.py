"""Provides a flask blueprint for REST calls for login
"""
from flask import Blueprint, request, url_for
from werkzeug.exceptions import HTTPException
from functools import wraps
import simplejson

import api
from providers import PROVIDERS

blueprint = Blueprint('rest.auth', __name__)

def jsonresult(fn):
    """Wraps the results (and any abort calls) in a json response"""
    @wraps(fn)
    def view(*args, **kwargs):
        try:
            return simplejson.dumps(fn(*args, **kwargs))
        except HTTPException as e:
            if not hasattr(e, 'data'):
                return simplejson.dumps({"error": e.get_description()}), e.code
            return simplejson.dumps(e.data), e.code
    return view

@blueprint.route('/')
def error():
    """errors sometimes don't get redirected to the oauth_callback for some reason. This
    exists simply to make sure the rest api still returns an empty page when that happens
    TODO: come up with a way to handle errors
    """
    return callback()

@blueprint.route('/__callback__/')
def callback():
    """An empty callback that desktop apps with embedded browsers can use to redirect to
    and pull the query parameters out of the browser without having an error message pop up.
    """
    return ""

@blueprint.route('/login/<string:provider>/init/')
@jsonresult
def init_login(provider):
    """Initiates the Login procedure
    request.args:
        oauth_callback: the oauth_callback or redirect_uri that the provider should
                        redirect the user to. defaults to /__callback__/
    """
    callback = request.args.get('oauth_callback') or url_for('.callback', _external=True)
    return {"redirect": api.init_login(provider, callback)}

@blueprint.route('/login/<string:provider>/verify/')
@jsonresult
def verify_login(provider):
    user = api.verify_login(provider, **request.args)
    return user.to_dict()
