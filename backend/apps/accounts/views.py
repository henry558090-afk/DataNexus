from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import IsManager
from apps.accounts.serializers import UserSerializer
from apps.audit.services import log

User = get_user_model()


class LoginView(ObtainAuthToken):
    """账号密码换 Token，并记录登录审计。"""

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        log("login", user=user, request=request, target=user.username)
        return Response({"token": token.key})


class UserViewSet(viewsets.ModelViewSet):
    """用户管理（仅管理员）。辅助管理员看不到、也管不了超级管理员。"""

    serializer_class = UserSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        qs = User.objects.all().order_by("id")
        # 辅助管理员不能管理超级管理员
        if not self.request.user.is_superuser:
            qs = qs.exclude(is_superuser=True)
        return qs
