from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, MajorViewSet, ChapterViewSet, ExamGroupViewSet, ExerciseViewSet, UserViewSet, ExamViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'majors', MajorViewSet)
router.register(r'chapters', ChapterViewSet)
router.register(r'examgroups', ExamGroupViewSet)
router.register(r'users', UserViewSet)
router.register(r'exams', ExamViewSet)
# router.register(r'exercises', ExerciseViewSet, basename='exercise')  # 为普通列表指定 basename
router.register(r'examgroups/(?P<examgroup_id>\d+)/exercises', ExerciseViewSet, basename='examgroup-exercise')

urlpatterns = [
    path('', include(router.urls)),
]