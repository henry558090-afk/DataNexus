from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import IsManager
from apps.datasource.models import DataSource
from apps.datasource.serializers import DataSourceSerializer
from core import oracle_client


def _test(params: oracle_client.OracleConnParams) -> Response:
    """统一执行连接测试并返回结果（失败不抛 500，返回 ok=False + 原因）。"""
    try:
        oracle_client.test_connection(params)
        return Response({"ok": True, "message": "连接成功"})
    except Exception as exc:  # noqa: BLE001 - 对外返回失败原因
        return Response({"ok": False, "message": str(exc)})


class DataSourceViewSet(viewsets.ModelViewSet):
    """数据源管理（仅管理员）。密码加密存储、永不回显。"""

    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    permission_classes = [IsManager]

    @action(detail=True, methods=["post"])
    def test(self, request: Request, pk: str | None = None) -> Response:
        """测试已保存数据源的连接。"""
        ds = self.get_object()
        params = oracle_client.OracleConnParams(
            host=ds.host,
            port=ds.port,
            service_name=ds.service_name,
            user=ds.username,
            password=ds.password,
        )
        return _test(params)

    @action(detail=False, methods=["post"], url_path="test-connection")
    def test_connection(self, request: Request) -> Response:
        """用表单参数测试连接（保存前预检）。"""
        d = request.data
        try:
            params = oracle_client.OracleConnParams(
                host=d["host"],
                port=int(d["port"]),
                service_name=d["service_name"],
                user=d["username"],
                password=d.get("password", ""),
            )
        except (KeyError, ValueError, TypeError):
            return Response({"ok": False, "message": "连接参数不完整"})
        return _test(params)
