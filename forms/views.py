from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import FormType, FormSchema,SchemaStatus
from .serializers import FormTypeSerializer, FormSchemaCreateSerializer
from .permissions import IsAdmin
from .permissions import IsAdminOrReadOnlyForStaff


class FormTypeViewSet(ModelViewSet):
    queryset = FormType.objects.all()
    serializer_class = FormTypeSerializer
    permission_classes = [IsAdminOrReadOnlyForStaff]


class FormSchemaViewSet(ModelViewSet):
    queryset = FormSchema.objects.select_related("form_type")
    serializer_class = FormSchemaCreateSerializer
    permission_classes = [IsAdminOrReadOnlyForStaff]

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        schema = self.get_object()

        FormSchema.objects.filter(
            form_type=schema.form_type,
            status=SchemaStatus.ACTIVE
        ).update(status=SchemaStatus.INACTIVE)

        schema.status = SchemaStatus.ACTIVE
        schema.save(update_fields=["status"])

        return Response({"detail": "Schema activated"})
