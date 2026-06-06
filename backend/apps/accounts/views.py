from django.contrib.auth import get_user_model
from rest_framework import viewsets

from apps.accounts.permissions import IsManager
from apps.accounts.serializers import UserSerializer

User = get_user_model()


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
