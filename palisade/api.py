from flask import abort as flask_abort
from werkzeug.exceptions import HTTPException
from providers import PROVIDERS

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

def _get_provider(provider):
    prov = PROVIDERS.get(provider)
    if prov is None:
        abort(400, error='unsupported oauth provider `%s`' % provider)
    return prov

def init_login(provider, callback):
    return _get_provider(provider).get_redirect(callback)

def verify_login(provider, oauth_verifier=None, code=None, error=None, **unused_kwargs):
    prov = _get_provider(provider)
    args = {}
    if error is not None:
        abort(401, error=error)
    elif oauth_verifier is not None:
        args['oauth_verifier'] = oauth_verifier
    elif code is not None:
        args['code'] = code
    else:
        abort(400, error='login to requires `oauth_verifier` or `code` argument')
    
    try:
        user = prov.verify(**args)
        return user
    except KeyError:
        abort(400, error='invalid session passed')
