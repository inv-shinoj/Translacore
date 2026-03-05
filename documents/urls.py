from django.urls import path
from .views import DocumentListCreateView, DocumentDetailView, DocumentDownloadView

urlpatterns = [
    path(
        "",
        DocumentListCreateView.as_view(),
        name="document-list-create",
    ),
    path(
        "<uuid:doc_id>/",
        DocumentDetailView.as_view(),
        name="document-detail",
    ),
    path(
        "<uuid:doc_id>/download/<str:file_kind>/",
        DocumentDownloadView.as_view(),
        name="document-download",
    ),
]
