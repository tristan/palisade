from flask import Blueprint, request, url_for, abort as flask_abort
from werkzeug.exceptions import HTTPException
from functools import wraps
import simplejson

from palisade.providers import PROVIDERS

blueprint = Blueprint('rest', __name__)

def abort(code, **kwargs):
    """
    Wraps the flask abort function to support adding kwargs to the error
    """
    try:
        flask_abort(code)
    except HTTPException as e:
        if len(kwargs):
            e.data = kwargs
        raise e

def jsonresult(fn):
    """
    Wraps the results (and any abort calls) in a json response
    """
    @wraps(fn)
    def view(*args, **kwargs):
        try:
            return simplejson.dumps(fn(*args, **kwargs))
        except HTTPException as e:
            return simplejson.dumps(e.data), e.code
    return view

@blueprint.route('/__callback__/')
def default_callback():
    return ""

@blueprint.route('/login/<string:provider>/init/')
@jsonresult
def init_login(provider):
    oauth_callback = request.args.get('oauth_callback')
    if oauth_callback is None:
        oauth_callback = url_for('.default_callback', _external=True)

    prov = PROVIDERS.get(provider)
    if prov is None:
        abort(400, error='unsupported oauth provider `%s`' % provider)
        
    return {"redirect": prov.get_redirect(oauth_callback)}

@blueprint.route('/login/<string:provider>/verify/')
@jsonresult
def verify_login(provider):
    oauth_token = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')
    code = request.args.get('code')

    prov = PROVIDERS.get(provider)
    if prov is None:
        abort(400, error='unsupported oauth provider `%s`' % provider)

    # make sure we have a verifier or code argument
    if oauth_verifier is None and code is None:
        abort(400, error='login to requires `oauth_verifier` or `code` argument')

    try:
        user = prov.verify(**request.args)
        return {
            "user_id": user.id,
            "user_name": user.name
        }
    except KeyError:
        abort(400, error='invalid session passed')
