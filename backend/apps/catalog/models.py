from django.conf import settings
from django.db import models


class Department(models.Model):
    """部门 = 一组用户。用户可属于多个部门。"""

    name = models.CharField("部门名", max_length=100, unique=True)
    order = models.IntegerField("排序", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "部门"
        verbose_name_plural = "部门"

    def __str__(self) -> str:
        return self.name


class Folder(models.Model):
    """文件夹（多层目录树）。文件放在文件夹里；文件夹可授权给部门或个人。"""

    name = models.CharField("名称", max_length=150)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="上级文件夹",
    )
    order = models.IntegerField("排序", default=0)
    # 是否允许无权限用户在门户里看到此目录名并发起访问申请（v0.27 审批闭环）。
    # 默认 False：未标记的目录对无权限用户完全不可见、不可申请。
    requestable = models.BooleanField("可被申请", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "文件夹"
        verbose_name_plural = "文件夹"

    def __str__(self) -> str:
        return self.name

    def ancestor_ids(self) -> list[int]:
        """自身 + 所有祖先的 id（用于授权递归判定）。

        一次查询载入全部 (id, parent_id) 后在内存里上溯，避免逐级懒加载的
        N 次查询（v0.22 M3）。内部目录树规模小，单次全量加载远优于 N+1。
        含环保护：parent 链出现重复 id 即停止。
        """
        parent_map = dict(Folder.objects.values_list("id", "parent_id"))
        ids = [self.id]
        seen = {self.id}
        pid = parent_map.get(self.id)
        while pid is not None and pid not in seen:
            ids.append(pid)
            seen.add(pid)
            pid = parent_map.get(pid)
        return ids


class Favorite(models.Model):
    """用户收藏的文件夹（v0.24）。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites"
    )
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "folder")]
        verbose_name = "收藏"
        verbose_name_plural = "收藏"


class FolderShare(models.Model):
    """文件夹授权：把某文件夹分享给【部门】或【个人】，递归覆盖其子文件夹/文件。"""

    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="shares")
    subject_department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="folder_shares",
    )
    subject_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="folder_shares",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "文件夹授权"
        verbose_name_plural = "文件夹授权"

    def __str__(self) -> str:
        subject = self.subject_department_id or f"user:{self.subject_user_id}"
        return f"folder#{self.folder_id} -> {subject}"
