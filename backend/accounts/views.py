from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


def issue_token(user):
    """get_or_create keeps login idempotent — same user always reuses one token."""
    token, _ = Token.objects.get_or_create(user=user)
    return token.key


class RegisterView(APIView):
    """POST /api/auth/register/ — create an account and sign in immediately."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = issue_token(user)
        return Response(
            {'token': token, 'user': UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """POST /api/auth/login/ — username or email + password → token."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = issue_token(user)
        return Response({'token': token, 'user': UserSerializer(user).data})


class LogoutView(APIView):
    """POST /api/auth/logout/ — revoke the caller's token."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Token auth: request.auth is the Token instance (safe even for
        # session-authenticated admin logins where request.auth is None).
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
