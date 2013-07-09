from providers import PROVIDERS

def get_profile_url(provider, username):
    p = PROVIDERS[provider]
    if p is None:
        return None
    return p.get_user_profile_url(username)
