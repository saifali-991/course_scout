from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Public profile payload returned by Google login / me."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']
        read_only_fields = fields


class GoogleLoginSerializer(serializers.Serializer):
    """The credential is the ID token JWT Google Identity Services hands the
    browser after the user picks their account."""

    credential = serializers.CharField()