from rest_framework.routers import DefaultRouter
from .views import FormTypeViewSet, FormSchemaViewSet

router = DefaultRouter()
router.register("types", FormTypeViewSet)
router.register("schemas", FormSchemaViewSet)

urlpatterns = router.urls
