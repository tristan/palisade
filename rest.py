from flask import Blueprint, request, url_for, abort as flask_abort, session, redirect
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

@blueprint.route('/')
def api():
    return callback()

@blueprint.route('/__callback__/')
def callback():
    """proxy callback, used so providers always redirect back to /api/__callback__/ 
    (this is so we can work with providers that require a specific redirect url to be matched)

    TODO: I'm still playing with this. I'm not sure I like the idea if a goal of this service
    is to be run behind the scenes (i.e. behind a server), but it's fine if it's meant as a
    login system for desktop/mobile applications as well.
    """
    redirect_uri = request.args.get('callback', None)
    # we need to include the query in this redirect
    args = '&'.join('{0}={1}'.format(k, request.args[k]) for k in request.args if k != 'callback')
    if args:
        redirect_uri += '{0}{1}'.format(
            '?' if '?' not in redirect_uri else '&',
            args)
        
    if redirect_uri:
        return redirect(redirect_uri)
    return ""

@blueprint.route('/login/<string:provider>/init/')
@jsonresult
def init_login(provider):
    callback = request.args.get('oauth_callback')
    oauth_callback = url_for('.callback', callback=callback, _external=True)

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
