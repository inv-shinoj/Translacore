from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Project
from .serializers import ProjectCreateSerializer
from .permissions import CanCreateProject


class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectCreateSerializer
    permission_classes = [IsAuthenticated, CanCreateProject]
