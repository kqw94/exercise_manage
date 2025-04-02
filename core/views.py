from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import Category, Exercise, Exam, Major, Chapter, ExamGroup
from .serializers import CategorySerializer, ExerciseSerializer, UserSerializer, ExamSerializer, MajorSerializer, ChapterSerializer, ExamGroupSerializer

User = get_user_model()

# 自定义分页类
class StandardPagination(PageNumberPagination):
    page_size = 10  # 默认每页10条
    page_size_query_param = 'page_size'  # 客户端可通过 ?page_size= 指定
    max_page_size = 100  # 最大每页100条

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(is_active=True)  # 只返回活跃用户

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class MajorViewSet(viewsets.ModelViewSet):
    queryset = Major.objects.all()
    serializer_class = MajorSerializer

class ChapterViewSet(viewsets.ModelViewSet):
    queryset = Chapter.objects.all()
    serializer_class = ChapterSerializer

class ExamGroupViewSet(viewsets.ModelViewSet):
    queryset = ExamGroup.objects.all()
    serializer_class = ExamGroupSerializer

class ExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseSerializer
    pagination_class = StandardPagination
    queryset = Exercise.objects.all()  # 添加默认 queryset

    def get_queryset(self):
        examgroup_id = self.kwargs.get('examgroup_id') or self.request.query_params.get('examgroup_id')
        if examgroup_id:
            try:
                ExamGroup.objects.get(examgroup_id=examgroup_id)
                return Exercise.objects.filter(exam_group_id=examgroup_id)
            except ExamGroup.DoesNotExist:
                return Exercise.objects.none()
        return Exercise.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists() and 'examgroup_id' in request.query_params:
            return Response({"error": "Exam group not found or no exercises available"}, status=404)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)



class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    pagination_class = StandardPagination  # 可选，显式指定