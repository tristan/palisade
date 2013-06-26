import os
from fndb import db
import providers

class User(db.Expando):
    auth_ids = db.StringProperty(repeated=True)

    @staticmethod
    def generate_auth_id(provider, uid, subprovider=None):
        if subprovider is not None:
            provider = '{0}#{1}'.format(provider, subprovider)
        return '{0}:{1}'.format(provider, uid)

    @classmethod
    def get_or_create(cls, auth_id, update_missing_fields=False, ignore_invalid_keys=True, **user_details):
        user = cls.get_by_auth_id(auth_id)
        if user is None:
            user = cls(auth_ids=[auth_id])
            update_missing_fields = True
        if update_missing_fields:
            for key in user_details:
                if key in ['parent', 'id']:
                    if ignore_invalid_keys:
                        user_details.pop(key)
                    else:
                        raise Exception("Cannot create User Profile with reserved '%s' property" % key)
                else:
                    if getattr(user, key, None) is not None:
                        user_details.pop(key)
            user.populate(**user_details)
            user.put()
        return user
        
    @classmethod
    def get_by_auth_id(cls, auth_id):
        return cls.query(cls.auth_ids == auth_id).get()

    @classmethod
    def get_by_provider_username(cls, provider, username):
        prov = providers.PROVIDERS.get(provider)
        if not prov:
            return None
        url = prov.get_user_profile_url(username)
        return cls.query(db.GenericProperty(provider) == url).get()

    @property
    def id(self):
        return self.key.id()

def register_profile(cls):
    for prop in cls._properties:
        User._properties[prop] = cls._properties[prop]

    uargs = dir(User)
    for arg in dir(cls):
        if arg not in uargs:
            setattr(User, arg, cls.__dict__[arg])
