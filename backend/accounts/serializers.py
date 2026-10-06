from django.contrib.auth import authenticate, get_user_model, password_validation
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Public profile payload returned by register / login / me."""

    saved_resources = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined', 'saved_resources']
        read_only_fields = fields

    def get_saved_resources(self, obj):
        # Placeholder until Saved moves server-side; keeps the payload stable.
        return []


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_blank=True, default='')
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def validate_username(self, value):
        if not value.isalnum():
            raise serializers.ValidationError('Username must be letters and numbers only.')
        return value

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Accepts a username OR an email in the same `identifier` field."""

    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        identifier = (attrs.get('identifier') or '').strip()
        password = attrs.get('password') or ''

        # Email login → resolve to the username Django's authenticate() wants.
        username = identifier
        if '@' in identifier:
            match = User.objects.filter(email__iexact=identifier).first()
            username = match.username if match else identifier

        user = authenticate(
            username=username,
            password=password,
        )
        if user is None:
            raise serializers.ValidationError(
                'Invalid username/email or password.'
            )
        if not user.is_active:
            raise serializers.ValidationError('This account is disabled.')
        attrs['user'] = user
        return attrs
