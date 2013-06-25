import os
from fndb import db

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

    @property
    def id(self):
        return self.key.id()
