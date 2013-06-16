import rauth.service # import OAuth2Service, OAuth1Service, 
from rauth.service import parse_utf8_qsl
from flask import session
from models import User

# TODO: better way to do this ...
import palisade.settings# as settings
class _x_config(object):
    def __init__(self, settings):
        self.config = settings.__dict__

app = _x_config(palisade.settings)

class OAuthServiceWrapper(object):
    def __init__(self, name, base_url, request_token_url, access_token_url, 
                 authorize_url, profile_url, profile_key_mappings = {},
                 profile_kwargs = {}, authorize_kwargs = {},
                 **kwargs):
        self.name = name
        self.base_url = base_url
        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorize_url = authorize_url
        self.profile_url = profile_url
        self.profile_key_mappings = profile_key_mappings
        self.profile_kwargs = profile_kwargs
        self.authorize_kwargs = authorize_kwargs

    def get_or_create_user(self, token=None):
        if token is None:
            token = session.get('oauth_token')
            if token is None:
                raise Exception("Error getting user's oauth token")

        res = self.service.get_session(token).get(self.profile_url, params=self.profile_kwargs)
        if res.status_code != 200:
            raise Exception("Error getting user's credentials")
        user_info = res.json()

        profile = {}
        for k,v in self.profile_key_mappings.items():
            if isinstance(v, basestring):
                profile[k] = user_info.get(v)
            elif isinstance(v, list):
                profile[k] = reduce(
                    lambda x,k: x is not None and x.get(k, None) or None, 
                    v,
                    user_info)
            elif hasattr(v, '__call__'):
                profile[k] = v(user_info)
            else:
                #TODO: should probably throw some kind of error here
                pass

        # make sure email field is always in the profile
        # TODO: should probably just make it an actual property of the model
        if 'email' not in profile:
            profile['email'] = None

        # TODO: is user_info.id always present for every provider? if not what should we do here?
        profile['auth_id'] = User.generate_auth_id(self.name, 
                                                   profile.pop('id', user_info['id']))

        user = User.get_or_create(**profile)
        return user


class OAuth1Service(OAuthServiceWrapper):
    def __init__(self, name, consumer_key, consumer_secret, **kwargs):
        super(OAuth1Service, self).__init__(name, **kwargs)
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        kwargs.pop('name', None)
        kwargs.pop('profile_url', None)
        kwargs.pop('profile_key_mappings', None)
        kwargs.pop('profile_kwargs', None)
        kwargs.pop('authorize_kwargs', None)

        self.service = rauth.service.OAuth1Service(
            self.consumer_key,
            self.consumer_secret,
            **kwargs)

    def get_redirect(self, oauth_callback=None):
        # fetch the request_token (token and secret 2-tuple) and convert it to a dict
        request_token = self.service.get_request_token(data={'oauth_callback': oauth_callback})
        session['request_token'] = request_token
        return self.service.get_authorize_url(request_token[0])

    def verify(self, oauth_verifier, **kwargs):
        request_token, request_token_secret = session.pop('request_token')
        token = self.service.get_access_token(
            request_token,
            request_token_secret,
            method="GET",
            data={"oauth_verifier": oauth_verifier})
        session['oauth_token'] = token
        return self.get_or_create_user(token)

PROVIDERS = {}
PROVIDERS['twitter'] = {
    'consumer_key': app.config.get('TWITTER_CONSUMER_KEY'),
    'consumer_secret': app.config.get('TWITTER_CONSUMER_SECRET'),
    'base_url': 'https://api.twitter.com/1.1/',
    'request_token_url': 'https://api.twitter.com/oauth/request_token',
    'access_token_url': 'https://api.twitter.com/oauth/access_token',
    'authorize_url': 'https://api.twitter.com/oauth/authenticate',
    'profile_url': 'account/verify_credentials.json',
    'profile_key_mappings': {
        'name' : lambda x: x.get('name', x.get('screen_name')),
        'twitter': lambda x: 'http://twitter.com/' + x.get('screen_name'),
        'location': 'location',
        'avatar': 'profile_image_url'
    }
}

for name in PROVIDERS:
    p = PROVIDERS[name]
    if p.get('consumer_key') is not None and p.get('consumer_secret') is not None:
        p = OAuth1Service(name=name,**p)
    else:
        p = None
    PROVIDERS[name] = p
