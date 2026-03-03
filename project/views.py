from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Project
from .serializers import ProjectCreateSerializer, ProjectListSerializer
from .permissions import CanCreateProject, CanListAllProject


class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.select_related(
        "form_schema__form_type", "created_by"
    ).all()
    permission_classes = [IsAuthenticated, CanListAllProject]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProjectCreateSerializer
        return ProjectListSerializer
