
from allauth.account.adapter import DefaultAccountAdapter

class NoMessageAccountAdapter(DefaultAccountAdapter):
    def add_message(self, request, level, message_template, message_context=None, extra_tags=''):
        # Ignore all messages from allauth
        pass

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from django.shortcuts import redirect
from allauth.exceptions import ImmediateHttpResponse

class AdminOnlySocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return False  # Prevent new accounts from being created

    def pre_social_login(self, request, sociallogin):
        # If the user's social account is already connected to an existing user, let them in.
        if sociallogin.is_existing:
            return

        # Get the email from the Google response
        email = sociallogin.account.extra_data.get('email', '').lower()
        if not email:
            raise ImmediateHttpResponse(redirect('unauthorized_access'))

        # Check if we already have a user in the database with this email
        try:
            user = User.objects.get(email__iexact=email)
            # Auto-connect this new social login to the existing user
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            # If the email is not in the database, deny access!
            raise ImmediateHttpResponse(redirect('unauthorized_access'))
