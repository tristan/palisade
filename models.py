import os

class User(object):
    @staticmethod
    def generate_auth_id(provider, uid, subprovider=None):
        if subprovider is not None:
            provider = '{0}#{1}'.format(provider, subprovider)
        return '{0}:{1}'.format(provider, uid)

    @classmethod
    def get_by_auth_id(cls, auth_id):
        raise NotImplementedError
        
    @classmethod
    def get_or_create(cls, auth_id, ignore_invalid_keys=True, **user_details):
        raise NotImplementedError

    def put(self):
        raise NotImplementedError

    @property
    def id(self):
        raise NotImplementedError

if 'SERVER_SOFTWARE' in os.environ:
    # TODO: GAE Models for user
    pass
else:
    class Dict_Expando(dict):
        def __init__(self, **kwargs):
            self.update(kwargs)
        def __getattr__(self, name):
            return self.get(name)
        def __setattr__(self, name, value):
            self[name] = value

    users = dict()
    class Dict_User(User, Dict_Expando):
        @classmethod
        def get_by_auth_id(cls, auth_id):
            return users.get(auth_id)

        @classmethod
        def get_or_create(cls, auth_id, ignore_invalid_keys=True, **user_details):
            user = cls.get_by_auth_id(auth_id)
            if user is None:
                user = cls(auth_ids=[auth_id], **user_details)
            user.put()
            return user

        def put(self):
            for aid in self.auth_ids:
                users[aid] = self

        @property
        def id(self):
            return self.get('auth_ids', [None])[0]

    User = Dict_User
