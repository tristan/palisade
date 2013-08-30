import rauth.service # import OAuth2Service, OAuth1Service, 
from rauth.service import parse_utf8_qsl
from flask import session
import re
import sys

# TODO: better way to do this ...
import palisade.settings# as settings
class _x_config(object):
    def __init__(self, settings):
        self.config = settings.__dict__

app = _x_config(palisade.settings)

def generate_auth_id(provider, uid, subprovider=None):
    if subprovider is not None:
        provider = '{0}#{1}'.format(provider, subprovider)
    return '{0}:{1}'.format(provider, uid)

class OAuthServiceWrapper(object):
    def __init__(self, name, base_url, access_token_url, 
                 authorize_url, profile_url, user_url_template, request_token_url=None,
                 profile_key_mappings = {}, profile_kwargs = {}, 
                 authorize_kwargs = {}, **kwargs):
        self.name = name
        self.base_url = base_url
        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorize_url = authorize_url
        self.user_url_template = user_url_template
        self.profile_url = profile_url
        self.profile_key_mappings = profile_key_mappings
        self.profile_kwargs = profile_kwargs
        self.authorize_kwargs = authorize_kwargs

        if 'gevent' in sys.modules and sys.modules['gevent'].version_info < (1, 0, 0):
            # NOTE: there seems to be some issues with the gevent dns stack which breaks requests session
            # calls. forcing a dns resolve on the host seems to fix the issues
            import gevent, requests
            gevent.dns.resolve_ipv4(requests.utils.urlparse(self.base_url).hostname)
    
    def get_user_profile_url(self, username):
        return self.user_url_template % username

    def get_user_profile(self, token):
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
        profile['id'] = profile.get('id', user_info['id'])
        profile['auth_id'] = generate_auth_id(self.name, profile['id'])

        return profile

    def get(self, token, url, params={}, **kwargs):
        return self.service.get_session(token).get(url, params=params, **kwargs)
    def post(self, token, url, params={}, **kwargs):
        return self.service.get_session(token).post(url, params=params, **kwargs)
    def delete(self, token, url, params={}, **kwargs):
        return self.service.get_session(token).delete(url, params=params, **kwargs)

class OAuth1Service(OAuthServiceWrapper):
    def __init__(self, name, consumer_key, consumer_secret, **kwargs):
        super(OAuth1Service, self).__init__(name, **kwargs)
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        kwargs.pop('name', None)
        kwargs.pop('user_url_template', None)
        kwargs.pop('profile_url', None)
        kwargs.pop('profile_key_mappings', None)
        kwargs.pop('profile_kwargs', None)
        kwargs.pop('authorize_kwargs', None)

        self.service = rauth.service.OAuth1Service(
            self.consumer_key,
            self.consumer_secret,
            **kwargs)

    def get_redirect(self, oauth_callback=None, **kwargs):
        # fetch the request_token (token and secret 2-tuple) and convert it to a dict
        data = kwargs or {}
        data['oauth_callback'] = oauth_callback
        request_token = self.service.get_request_token(data=data)
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
        return self.get_user_profile(token)

class OAuth2Service(OAuthServiceWrapper):
    def __init__(self, name, client_id, client_secret, **kwargs):
        super(OAuth2Service, self).__init__(name, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret

        kwargs.pop('name', None)
        kwargs.pop('user_url_template', None)
        kwargs.pop('profile_url', None)
        kwargs.pop('profile_key_mappings', None)
        kwargs.pop('profile_kwargs', None)
        kwargs.pop('authorize_kwargs', None)

        self.service = rauth.service.OAuth2Service(
            self.client_id,
            self.client_secret,
            **kwargs)

    def get_redirect(self, redirect_uri=None, **kwargs):
        # fetch the request_token (token and secret 2-tuple) and convert it to a dict
        session['oauth2_redirect_uri'] = redirect_uri 
        #request_token = self.service.get_request_token(data={'oauth_callback': oauth_callback})
        return self.service.get_authorize_url(redirect_uri=redirect_uri, **kwargs)

    def verify(self, code, **kwargs):
        key = {
            'code': code,
            'redirect_uri': session.pop('oauth2_redirect_uri', None)
        }
        token = self.service.get_access_token(
            method='GET', params=key
        )
        session['oauth_token'] = token
        return self.get_user_profile(token)

PROVIDERS = {}
PROVIDERS['twitter'] = {
    'consumer_key': app.config.get('TWITTER_CONSUMER_KEY'),
    'consumer_secret': app.config.get('TWITTER_CONSUMER_SECRET'),
    'base_url': 'https://api.twitter.com/1.1/',
    'request_token_url': 'https://api.twitter.com/oauth/request_token',
    'access_token_url': 'https://api.twitter.com/oauth/access_token',
    'authorize_url': 'https://api.twitter.com/oauth/authenticate',
    'user_url_template': 'http://twitter.com/%s',
    'profile_url': 'account/verify_credentials.json',
    'profile_key_mappings': {
        'name' : lambda x: x.get('name', x.get('screen_name')),
        'profile_url': lambda x: 'http://twitter.com/' + x.get('screen_name'),
        'location': 'location',
        'avatar': 'profile_image_url'
    }
}
PROVIDERS['facebook'] = {
    'client_id': app.config.get('FACEBOOK_CLIENT_ID'),
    'client_secret': app.config.get('FACEBOOK_CLIENT_SECRET'),
    'base_url': 'https://graph.facebook.com/',
    'access_token_url': 'https://graph.facebook.com/oauth/access_token',
    'authorize_url': 'https://graph.facebook.com/oauth/authorize',
    'user_url_template': 'http://www.facebook.com/%s',
    'profile_url': 'me',
    'profile_kwargs': {'fields':'name,link,location,email,picture'},
    'profile_key_mappings': {
        'name' : lambda x: x.get('name', x.get('username')),
        # normalise facebook link so it always starts with http:// 
        'profile_url': lambda x: (lambda m: 'http{0}'.format(m.group(1)) if m else '')(re.match('^https?(.*)', x.get('link', ''))),
        'location': ['location', 'name'],
        'email' : 'email',
        'avatar': ['picture', 'data', 'url']
    }
}
PROVIDERS['github'] = {
    'client_id': app.config.get('GITHUB_CLIENT_ID'),
    'client_secret': app.config.get('GITHUB_CLIENT_SECRET'),
    'base_url': 'https://api.github.com/',
    'access_token_url': 'https://github.com/login/oauth/access_token',
    'authorize_url': 'https://github.com/login/oauth/authorize',
    'user_url_template': 'http://github.com/%s',
    'profile_url': 'user',
    'profile_key_mappings': {
        'name' : lambda x: x.get('name', x.get('login')),
        'profile_url': lambda x: 'http://github.com/' + x.get('login'),
        'location': 'location',
        'email' : 'email',
        'avatar': 'avatar_url'
    }
}

for name in PROVIDERS:
    p = PROVIDERS[name]
    if p.get('consumer_key') is not None and p.get('consumer_secret') is not None:
        p = OAuth1Service(name=name,**p)
    elif p.get('client_id') is not None and p.get('client_secret') is not None:
        p = OAuth2Service(name=name,**p)
    else:
        p = None
    PROVIDERS[name] = p
