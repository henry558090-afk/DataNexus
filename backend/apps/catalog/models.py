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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "文件夹"
        verbose_name_plural = "文件夹"

    def __str__(self) -> str:
        return self.name

    def ancestor_ids(self) -> list[int]:
        """自身 + 所有祖先的 id（用于授权递归判定）。"""
        ids = [self.id]
        node = self.parent
        while node is not None:
            ids.append(node.id)
            node = node.parent
        return ids


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
