# core/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from .models import (
    Category, Major, Chapter, ExamGroup, Exercise, ExerciseAnswer, ExerciseAnalysis
)
from .serializers import (
    CategorySerializer, MajorSerializer, ChapterSerializer, ExamGroupSerializer,
    ExerciseSerializer, ExerciseAnswerSerializer, ExerciseAnalysisSerializer
)

# 自定义分页类
class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# 新增：显示所有 Category
class CategoryList(APIView):
    pagination_class = StandardPagination

    def get(self, request):
        categories = Category.objects.all()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(categories, request)
        serializer = CategorySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

# 1. 根据 category_id 获取 major 列表
class MajorListByCategory(APIView):
    pagination_class = StandardPagination

    def get(self, request, category_id):
        try:
            majors = Major.objects.filter(category_id=category_id)
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(majors, request)
            serializer = MajorSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

# 2. 根据 major_id 获取 chapter 列表
class ChapterListByMajor(APIView):
    pagination_class = StandardPagination

    def get(self, request, major_id):
        try:
            chapters = Chapter.objects.filter(major_id=major_id)
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(chapters, request)
            serializer = ChapterSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Major.DoesNotExist:
            return Response({"error": "Major not found"}, status=status.HTTP_404_NOT_FOUND)

# 3. 根据 chapter_id 获取 examgroup 列表
class ExamGroupListByChapter(APIView):
    pagination_class = StandardPagination

    def get(self, request, chapter_id):
        try:
            exam_groups = ExamGroup.objects.filter(chapter_id=chapter_id)
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(exam_groups, request)
            serializer = ExamGroupSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Chapter.DoesNotExist:
            return Response({"error": "Chapter not found"}, status=status.HTTP_404_NOT_FOUND)

# 4. 根据 category/major/chapter/examgroup 获取 exercise 列表（包含 questions）
class ExerciseList(APIView):
    pagination_class = StandardPagination

    def get(self, request):
        category_id = request.query_params.get('category_id')
        major_id = request.query_params.get('major_id')
        chapter_id = request.query_params.get('chapter_id')
        examgroup_id = request.query_params.get('examgroup_id')

        # 使用 prefetch_related 预加载 questions
        exercises = Exercise.objects.all().prefetch_related('questions')

        if category_id:
            exercises = exercises.filter(category_id=category_id)
        if major_id:
            exercises = exercises.filter(major_id=major_id)
        if chapter_id:
            exercises = exercises.filter(chapter_id=chapter_id)
        if examgroup_id:
            exercises = exercises.filter(exam_group_id=examgroup_id)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(exercises, request)
        serializer = ExerciseSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

# 5. 根据 exercise_id 获取答案列表
class AnswerListByExercise(APIView):
    pagination_class = StandardPagination

    def get(self, request, exercise_id):
        try:
            answers = ExerciseAnswer.objects.filter(exercise_id=exercise_id)
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(answers, request)
            serializer = ExerciseAnswerSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exercise.DoesNotExist:
            return Response({"error": "Exercise not found"}, status=status.HTTP_404_NOT_FOUND)
        

class AnalysisListByExercise(APIView):
    pagination_class = StandardPagination

    def get(self, request, exercise_id):
        try:
            analyses = ExerciseAnalysis.objects.filter(exercise_id=exercise_id)
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(analyses, request)
            serializer = ExerciseAnalysisSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exercise.DoesNotExist:
            return Response({"error": "Exercise not found"}, status=status.HTTP_404_NOT_FOUND)