import ipaddress

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


def mask_ip_address(ip: str) -> str | None:
    """
    Return the IP address with its first segment zeroed out for privacy.
    IPv4: 192.168.1.5  -> 0.168.1.5
    IPv6: 2001:db8::1  -> 0:db8::1
    """
    if not ip:
        return None
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return None
    if addr.version == 4:
        parts = ip.split(".")
        parts[0] = "0"
        return ".".join(parts)
    # IPv6 – zero the first group
    # Expand so we always have 8 groups before masking
    expanded = ipaddress.ip_address(ip).exploded
    parts = expanded.split(":")
    parts[0] = "0000"
    return ":".join(parts)


class DocumentDownloadLog(models.Model):
    document_type = models.ForeignKey(
        "analytics.DocumentTypeKey",
        verbose_name=_("document type"),
        to_field="key",
        db_column="document_type",
        on_delete=models.PROTECT,
        related_name="download_logs",
    )
    # PK of the source record – nullable for purely external documents
    object_id = models.PositiveIntegerField(
        verbose_name=_("object id"),
        null=True,
        blank=True,
        db_index=True,
    )
    url = models.URLField(
        verbose_name=_("url"),
        max_length=2000,
    )
    source = models.ForeignKey(
        "analytics.DocumentSourceKey",
        verbose_name=_("source"),
        to_field="key",
        db_column="source",
        on_delete=models.PROTECT,
        related_name="download_logs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="document_download_logs",
    )
    downloaded_at = models.DateTimeField(
        verbose_name=_("downloaded at"),
        auto_now_add=True,
        db_index=True,
    )
    # First segment zeroed; e.g. 0.168.1.5 for IPv4
    ip_address = models.GenericIPAddressField(
        verbose_name=_("ip address"),
        null=True,
        blank=True,
        unpack_ipv4=True,
    )

    class Meta:
        verbose_name = _("document download log")
        verbose_name_plural = _("document download logs")
        ordering = ("-downloaded_at",)

    def __str__(self):
        return f"{self.document_type} / {self.object_id} @ {self.downloaded_at}"


class DocumentTypeKey(models.Model):
    key = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = _("document type key")
        verbose_name_plural = _("document type keys")
        ordering = ("key",)

    def __str__(self):
        return self.key


class DocumentSourceKey(models.Model):
    key = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = _("document source key")
        verbose_name_plural = _("document source keys")
        ordering = ("key",)

    def __str__(self):
        return self.key
