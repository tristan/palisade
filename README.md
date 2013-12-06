# Palisade

A flask Blueprint to provide authentication via oauth and manage user profiles.

### setup

```
pip install flask flask-kvsession flask-failsafe simplejson
```

### configuration

###### Add OAuth variables to your flask app's configuration for any OAuth providers you want to support (see support for the specific provider for how to get these keys).

twitter:
```
TWITTER_CONSUMER_KEY = '<Twitter Consumer key>'
TWITTER_CONSUMER_SECRET = '<Twitter Consumer secret>'
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

### usage

##### view decorators

```
# create you app's blueprint
blueprint = Blueprint('your_app', __name__)

# register a route for init_login, your app should send a user here to initiate
# the login procedure with the oauth provider. You can either do this manually
# if you want to do something with the redirect_url before it's passed to the
# user like this:
@blueprint.route('/login/<string:provider>/')
@palisade.init_login('your_app.verify_login')
def init_login(redirect_url):
    # redirect the user to the providers authorisation page
    return redirect(redirect_url)
# or you can use `add_url_rule` like this:
blueprint.add_url_rule(
    '/login/<string:provider>/', 'init_login',
    palisade.init_login('your_app.verify_login', redirect=True)
)

# register the route that the oauth provider will redirect back to when the user
# authorises your app
@blueprint.route('/login/<string:provider>/verify/')
@palisade.verify_login
def verify_login(user_profile):
	# create a user based off the returned profile
	user = YourUserModel.get_or_create(**user_profile)
    # gets the user's id and stores in the session (see below for why)
    session['user_id'] = user.id
    return redirect(url_for('your_app.index'))

# to handle cases where a user denies your app access
@blueprint.errorhandler(401)
def error_401(error):
    print error
    print error.data
    return redirect(url_for('you_app.index'))

# to automatically redirect a user to a login page if a session key isn't
# present, use `@palisade.require_login(key, endpoint, **endpoint_kwargs)`.
# e.g. if you want to automatically redirect a user to the twitter login page
@blueprint.route('/')
@palisade.require_login('user_id', 'snabel.init_login', provider='twitter')
def index():
    return render_template('index.html')
```

##### REST blueprint

```
from flask import Flask
app = Flask(__name__)
import palisade.rest
app.register_blueprint(palisade.rest.blueprint, url_prefix='/api')
app.run(host='127.0.0.1',port=8080,debug=True)
```

### example REST usage w/ curl

assuming the base url the rest blueprint is registerd to is `http://127.0.0.1:8080/api`

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

* add in additional providers

### brain dump of what I am trying to achieve with Palisade

This was born from my wanting to pull the auth system i was using in a flask app out into a reusable component. It seemed like an interesting idea to abstract the whole system out into a seperate service that could be unaccessable from the outside world similar to how data storage systems like redis/couchdb/etc work.

After implementing OAuth2.0 and thinking about desktop apps using the service I realised this is not going to work in reality for the following reasons:
 * OAuth services that require a callback URL to match a specific prefix require the user to be redirected back to the backend service. I have hacked around this and made something that works, but it requires the backend service to be visible to the outside world, and I don't like having to do the extra redirect.
 * Desktop apps will need direct access to the backend system, otherwise the frontend system needs to essentually re-implement everything the backend server does. It's also probably going to be a nightmare figuring out a way that the backend service can tell the front service that the desktop app is verified to use it.
 * I want REST access for everything....
 * The backend server doesn't send any user or service sensitive information (i.e. the services secret oauth keys) around anyway, so having it hidden isn't such a big deal.

Taking these things into consiteration I decided this would be better as a *blueprint* for a flask app. It can then use that apps *(f)*ndb store to handle user data, and each app can specify it's own oauth keys (and thus have direct redirect urls).
