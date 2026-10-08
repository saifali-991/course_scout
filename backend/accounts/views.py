import re

from django.conf import settings
from django.contrib.auth import get_user_model
from google.auth.transport.requests import Request
from google.oauth2 import id_token as google_id_token
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import GoogleLoginSerializer, UserSerializer

User = get_user_model()


def issue_token(user):
    """get_or_create keeps login idempotent — same user always reuses one token."""
    token, _ = Token.objects.get_or_create(user=user)
    return token.key


def username_from_email(email):
    """'raj.kumar@gmail.com' -> 'rajkumar', deduped with a numeric suffix.

    Google emails can contain dots/plus tags that Django's default username
    validator would reject, so we strip to [a-z0-9] and append 2, 3, ... when
    the name is taken (raj, raj2, raj3 …).
    """
    base = re.sub(r'[^a-z0-9]', '', (email or '').split('@')[0].lower()) or 'user'
    base = base[:140]  # User.username max_length=150, room for the suffix
    username = base
    n = 1
    while User.objects.filter(username__iexact=username).exists():
        n += 1
        username = f'{base}{n}'[:150]
    return username


class GoogleLoginView(APIView):
    """POST /api/auth/google/ — verify Google's ID token, sign in (and create
    the account on first login), then hand back the DRF session token.

    Verification (google-auth, Google's own library) checks the JWT signature
    against Google's rotating certificates, the expiry, and that `aud` equals
    our GOOGLE_CLIENT_ID — so a token minted for another site is rejected.
    """

    # Token-only: no session cookie means no CSRF preflight drama on POST.
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        client_id = (settings.GOOGLE_CLIENT_ID or '').strip()
        if not client_id:
            return Response(
                {'detail': 'Google login is not configured on this server (GOOGLE_CLIENT_ID missing).'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payload = google_id_token.verify_oauth2_token(
                serializer.validated_data['credential'],
                Request(),
                audience=client_id,
            )
        except ValueError:
            # Bad signature, expired, wrong audience, malformed …
            return Response(
                {'detail': 'Google sign-in failed — the credential is invalid or expired.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email = (payload.get('email') or '').strip().lower()
        if not email or not payload.get('email_verified', False):
            return Response(
                {'detail': 'Your Google account has no verified email address.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            user = User.objects.create_user(
                username=username_from_email(email),
                email=email,
            )  # no password — this account can only sign in via Google
        elif not user.is_active:
            return Response(
                {'detail': 'This account is disabled.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response({'token': issue_token(user), 'user': UserSerializer(user).data})


class LogoutView(APIView):
    """POST /api/auth/logout/ — revoke the caller's token."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.auth is not None:
            request.auth.delete()
        else:
            Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """GET /api/auth/me/ — who am I? 401 when the token is missing/invalid."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'user': UserSerializer(request.user).data})