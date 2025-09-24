import io
from typing import Any, Iterable

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from openpyxl import Workbook
from rest_framework import permissions, renderers, viewsets
from rest_framework.response import Response


def _user_has_access(user: Any) -> bool:
    """Allow superusers, regional admins, or users with Pending view permission."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    # Pending users permission (model view perm)
    if user.has_perm("registrations.view_pending"):
        return True
    # Regional admin via explicit relation or permission codename
    try:
        from api.models import UserRegion  # inline import to avoid cycles

        if UserRegion.objects.filter(user=user).exists():
            return True
    except Exception:
        pass
    # Fallback check: any perm codename starting with region_admin_
    region_admin_perms = Permission.objects.filter(codename__startswith="region_admin_")
    if user.user_permissions.filter(id__in=region_admin_perms).exists():
        return True
    if Group.objects.filter(id__in=user.groups.all()).filter(permissions__in=region_admin_perms).exists():
        return True
    return False


def _build_queryset(selected_group_ids: Iterable[int], include_superusers: bool):
    from django.contrib.auth import get_user_model

    User = get_user_model()

    qs = User.objects.all()

    # Build a single OR filter instead of union of QuerySets
    q = Q()
    if selected_group_ids:
        q |= Q(groups__in=selected_group_ids)
    if include_superusers:
        q |= Q(is_superuser=True)

    if q:
        qs = qs.filter(q)

    return qs.distinct().order_by("id")


def _render_csv(users_qs) -> HttpResponse:
    import csv

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="users_per_permission.csv"'
    writer = csv.writer(response)
    writer.writerow(["ID", "Username", "Email", "Name", "Organization", "Active", "Staff"])  # headers
    for u in users_qs:
        name = f"{u.first_name} {u.last_name}".strip()
        org = getattr(getattr(u, "profile", None), "org", "") or ""
        writer.writerow([u.id, u.username, u.email, name, org, u.is_active, u.is_staff])
    return response


def _render_xlsx(users_qs) -> HttpResponse:
    from openpyxl.worksheet.worksheet import Worksheet

    wb = Workbook()
    ws: Worksheet = wb.active  # type: ignore[assignment]
    # Avoid setting title if type checker is unsure
    try:
        ws.title = "Users"
    except Exception:
        pass
    headers = ["ID", "Username", "Email", "Name", "Organization", "Active", "Staff"]
    ws.append(headers)  # type: ignore[attr-defined]
    for u in users_qs:
        name = f"{u.first_name} {u.last_name}".strip()
        org = getattr(getattr(u, "profile", None), "org", "") or ""
        row = [u.id, u.username, u.email, name, org, u.is_active, u.is_staff]
        ws.append(row)  # type: ignore[attr-defined]

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    response = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="users_per_permission.xlsx"'
    return response


REPORT_TITLE = _("Users per permission")


@staff_member_required
def users_per_permission_view(request: HttpRequest):
    # Gate access for staff who also meet custom criteria
    if not _user_has_access(request.user):
        return HttpResponse(status=403)

    context = admin.site.each_context(request)
    context.update(
        {
            "title": REPORT_TITLE,
        }
    )

    all_groups = Group.objects.order_by("name")

    selected_group_ids = [int(gid) for gid in request.GET.getlist("groups") if gid.isdigit()]
    include_superusers = request.GET.get("include_superusers") == "1"
    export = request.GET.get("export")  # "csv" | "xlsx" | None

    users_qs = _build_queryset(selected_group_ids, include_superusers)

    if export == "csv":
        return _render_csv(users_qs)
    if export == "xlsx":
        return _render_xlsx(users_qs)

    # Regular HTML render
    context.update(
        {
            "groups": all_groups,
            "selected_group_ids": selected_group_ids,
            "include_superusers": include_superusers,
            "users": users_qs[:500],  # safety cap for UI
            "result_count": users_qs.count() if selected_group_ids or include_superusers else 0,
        }
    )
    return render(request, "admin/users_per_permission.html", context)


class UsersPerPermissionAccess(permissions.BasePermission):
    """DRF permission: allow only authenticated users that pass our custom access gate."""

    def has_permission(self, request, view):  # type: ignore[override]
        allowed = bool(request.user and request.user.is_authenticated and _user_has_access(request.user))
        return True if allowed else False


class UsersPerPermissionViewSet(viewsets.ViewSet):
    """Read-only endpoint that renders an admin-like page or exports CSV/XLSX."""

    renderer_classes = [renderers.TemplateHTMLRenderer, renderers.JSONRenderer]
    permission_classes = [UsersPerPermissionAccess]

    def list(self, request: HttpRequest):
        all_groups = Group.objects.order_by("name")
        raw_groups = request.query_params.getlist("groups")
        try:
            selected_group_ids = [int(g) for g in raw_groups if g]
        except ValueError:
            selected_group_ids = []

        include_superusers = str(request.query_params.get("include_superusers", "")).lower() in ("1", "true", "on", "yes")
        export = str(request.query_params.get("export", "")).lower()  # <-- define export

        users_qs = _build_queryset(selected_group_ids, include_superusers)

        if export == "csv":
            return _render_csv(users_qs)
        if export == "xlsx":
            return _render_xlsx(users_qs)

        context = admin.site.each_context(request)
        context.update(
            {
                "title": REPORT_TITLE,
                "groups": all_groups,
                "selected_group_ids": selected_group_ids,
                "include_superusers": include_superusers,
                "users": users_qs[:500],
                "result_count": users_qs.count() if selected_group_ids or include_superusers else 0,
            }
        )
        return Response(context, template_name="admin/users_per_permission.html")
