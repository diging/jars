from django.utils.translation import ugettext_lazy as _
from rest_framework import HTTP_HEADER_ENCODING, exceptions

import requests
from requests.auth import HTTPBasicAuth
from cookies.models import *
from social_django.models import UserSocialAuth
from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
logger = settings.LOGGER
logger.setLevel('DEBUG')
GITHUB = 'https://api.github.com'


class GithubTokenBackend(BaseAuthentication):
    keyword = 'GithubToken'
    model = None

    def authenticate(self, request):
        """
        Authenticate a user by their GitHub ID.
        """
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)
        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):

        try:
            client, client_secret, access_token = token.split(':')
        except:
            return
        print "access_token", access_token
        path = "{github}/applications/{client}/tokens/{access_token}".format(
            github=GITHUB,
            client=client,
            access_token=access_token)

        response = requests.get(path, auth=HTTPBasicAuth(client, client_secret))

        if response.status_code == 404:   # Not a valid token.
            return

        data = response.json()
        github_user_id = data.get('user', {}).get('id')
        try:
            auth = UserSocialAuth.objects.get(uid=github_user_id, provider='github')
        except UserSocialAuth.DoesNotExist: # No such user.
            return

        return auth.user, None