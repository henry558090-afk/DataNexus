from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.accounts.permissions import IsManager
from apps.accounts.serializers import UserSerializer
from apps.audit.services import log

User = get_user_model()


class LoginView(ObtainAuthToken):
    """账号密码换 Token：限流防爆破（SEC1）+ 每次登录轮换刷新 Token 有效期（SEC2）。"""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        user = serializer.validated_data["user"]
        # 轮换：删旧建新，刷新有效期；旧设备上的 token 随即失效（单活动会话）
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        log("login", user=user, request=request, target=user.username)
        return Response({"token": token.key})


class LogoutView(APIView):
    """登出：删除服务端 Token，使其立即失效（SEC2）。"""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WecomLoginView(APIView):
    """企业微信 SSO（v0.27）：返回扫码授权 URL，前端跳转。未启用则 400。"""

    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request: Request) -> Response:
        from apps.accounts import wecom

        if not wecom.is_enabled():
            return Response({"detail": "企业微信登录未启用"}, status=400)
        redirect_uri = request.query_params.get("redirect_uri") or request.build_absolute_uri(
            "/api/auth/wecom/callback/"
        )
        return Response({"url": wecom.authorize_url(redirect_uri)})


class WecomCallbackView(APIView):
    """企业微信回调（v0.27）：code → userid → 映射本地用户 → 发 Token → 跳前端带 token。"""

    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request: Request):
        from django.conf import settings
        from django.shortcuts import redirect

        from apps.accounts import wecom

        if not wecom.is_enabled():
            return Response({"detail": "企业微信登录未启用"}, status=400)
        code = request.query_params.get("code")
        if not code:
            return Response({"detail": "缺少 code"}, status=400)
        try:
            userid = wecom.exchange_code_for_userid(code)
        except Exception as exc:  # noqa: BLE001
            return Response({"detail": f"企微登录失败：{exc}"}, status=400)

        user = User.objects.filter(username=userid).first()
        if user is None:
            if not getattr(settings, "WECOM_AUTO_PROVISION", True):
                return Response({"detail": "用户不存在且未开启自动创建"}, status=403)
            user = User.objects.create_user(username=userid)
            user.set_unusable_password()
            user.save()
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        log("login", user=user, request=request, target=f"{user.username}(企微)")
        front = getattr(settings, "WECOM_REDIRECT_FRONTEND", "/")
        sep = "&" if "?" in front else "?"
        return redirect(f"{front}{sep}token={token.key}")


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
