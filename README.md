# Palisade

A simple service providing a session based rest interface to a user/authentication system.

This is currently meant to be accessible only by server based applications 
and not directly by users/clients, but this will probably change.

### setup

```
pip install flask flask-kvsession flask-failsafe simplejson urllib3
```

### configuration

create a `secret_keys.py` file and add the following keys as required:

Required by all (to be able to use flask's sessions):
```
SECRET_KEY = '<key>'
```
generate key (from the python console)
```
>>> import os
>>> os.urandom(24)
```

add OAuth variables to `secret_keys.py` for any OAuth providers you want to support

twitter:
```
TWITTER_COSUMER_KEY = '<Twitter Consumer key>'
TWITTER_COSUMER_SECRET = '<Twitter Consumer secret>'
```

facebook:
```
FACEBOOK_CLIENT_ID = '<Facebook App ID/API Key>'
FACEBOOK_CLIENT_SECRET = '<Facebook App Secret>'
```

github:
```
GITHUB_CLIENT_ID = '<Github Client ID>'
GITHUB_CLIENT_SECRET = '<Github Client Secret>'
```

### run w/ flask only

```
python palisade
```

### run w/ Google App Engine

* TODO

### example client usage w/ curl

```
curl -v -b cookies.txt -c cookies.txt http://127.0.0.1:8080/api/login/twitter/init/
```
* copy redirect_url value from the result and stick it in your web browser
* authorize your app
* when you get the error page up, copy the query section of the url (?oauth_token=xxx&oauth_verifier=xxx) and replace the query section of the following line with it:

```
curl -v -b cookies.txt -c cookies.txt http://127.0.0.1:8080/api/login/twitter/verify/?oauth_token=xxx&oauth_verifier=xxx
```
* you are now logged in (and can use the other /api/ calls


### TODO

* add in additional providers (only twitter supported so far)
* make everything configurable
* set/get user profile (with Expando style model)