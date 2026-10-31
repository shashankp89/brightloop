from django.urls import include, path

handler403 = "core.views.permission_denied"
handler404 = "core.views.not_found"

urlpatterns = [
    path("", include("core.urls")),
]
