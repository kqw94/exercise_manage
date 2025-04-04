# core/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Func
from django.db import models 
from .models import (
    Category, Major, Chapter, ExamGroup, Exercise, ExerciseAnswer, ExerciseAnalysis, Question, ExerciseStem
)
from .serializers import (
    CategorySerializer, MajorSerializer, ChapterSerializer, ExamGroupSerializer,
    ExerciseSerializer, ExerciseAnswerSerializer, ExerciseAnalysisSerializer, QuestionSerializer
)
import logging
logger = logging.getLogger(__name__)

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


# 4. 根据 category/major/chapter/examgroup 获取 exercise 列表（包含 questions），支持搜索
class ExerciseList(APIView):
    pagination_class = StandardPagination

    def get(self, request):
        category_id = request.query_params.get('category_id')
        major_id = request.query_params.get('major_id')
        chapter_id = request.query_params.get('chapter_id')
        examgroup_id = request.query_params.get('examgroup_id')
        search = request.query_params.get('search')
        search_type = request.query_params.get('search_type', 'id')

        # 使用 prefetch_related 预加载 questions
        exercises = Exercise.objects.all().prefetch_related('questions')

        # 过滤分类（先应用分类条件）
        if category_id:
            exercises = exercises.filter(category_id=category_id)
        if major_id:
            exercises = exercises.filter(major_id=major_id)
        if chapter_id:
            exercises = exercises.filter(chapter_id=chapter_id)
        if examgroup_id:
            exercises = exercises.filter(exam_group_id=examgroup_id)

        # 搜索逻辑（在分类过滤后应用搜索）
        if search:
            if search_type == 'id':
                exercises = exercises.filter(exercise_id=search)  # 精确匹配
            elif search_type == 'content':
                exercises = exercises.filter(
                    Q(stem__stem_content__icontains=search) |
                    Q(questions__question_answer__icontains=search) |
                    Q(answer__answer_content__icontains=search) |
                    Q(analysis__analysis_content__icontains=search)
                ).distinct()

        # 按 int(exercise_id) 排序，兼容 MySQL
        class Cast(Func):
            function = 'CAST'
            template = '%(function)s(%(expressions)s AS UNSIGNED)'
        exercises = exercises.annotate(id_int=Cast('exercise_id', output_field=models.IntegerField())).order_by('id_int')

        # 分页（在过滤和搜索后再应用）
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(exercises, request)
        serializer = ExerciseSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    
    def put(self, request, exercise_id=None):
        logger.debug(f"Received PUT request data: {request.data}")
        try:
            exercise = Exercise.objects.get(exercise_id=exercise_id)
            data = request.data

            # 更新 stem
            if 'stem' in data:
                if exercise.stem:
                    exercise.stem.stem_content = data['stem']
                    exercise.stem.save()
                else:
                    stem = ExerciseStem.objects.create(stem_content=data['stem'])
                    exercise.stem = stem

            # 更新 answer
            if 'answer' in data:
                answer_data = data['answer']
                if exercise.answer:
                    exercise.answer.answer_content = answer_data.get('answer_content', exercise.answer.answer_content)
                    exercise.answer.render_type = answer_data.get('render_type', exercise.answer.render_type)
                    exercise.answer.from_model = answer_data.get('from_model', exercise.answer.from_model)
                    exercise.answer.save()
                else:
                    exercise.answer = ExerciseAnswer.objects.create(**answer_data)

            # 更新 analysis
            if 'analysis' in data:
                analysis_data = data['analysis']
                if exercise.analysis:
                    exercise.analysis.analysis_content = analysis_data.get('analysis_content', exercise.analysis.analysis_content)
                    exercise.analysis.render_type = analysis_data.get('render_type', exercise.analysis.render_type)
                    exercise.analysis.save()
                else:
                    exercise.analysis = ExerciseAnalysis.objects.create(**analysis_data)

            # 更新 questions
            if 'questions' in data:
                questions_data = data['questions']
                logger.debug(f"Questions data: {questions_data}")
                for q_data in questions_data:
                    try:
                        # 根据 exercise 和 question_order 定位 question
                        question = Question.objects.get(
                            exercise=exercise,
                            question_order=q_data['question_order']
                        )
                        # 更新 question_answer
                        if 'question_answer' in q_data:
                            question.question_answer = q_data['question_answer']
                            question.save()
                            logger.debug(f"Updated question {question.question_order}: {question.question_answer}")
                    except Question.DoesNotExist:
                        logger.warning(f"Question with order {q_data['question_order']} not found for exercise {exercise_id}")
                        # 可选：创建新 question
                        Question.objects.create(
                            exercise=exercise,
                            question_order=q_data['question_order'],
                            question_stem=q_data.get('question_stem', ''),
                            question_answer=q_data.get('question_answer', ''),
                            question_analysis=q_data.get('question_analysis', None)
                        )

            exercise.save()
            # 返回更新后的数据
            serializer = ExerciseSerializer(exercise)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exercise.DoesNotExist:
            return Response({"error": "Exercise not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating exercise {exercise_id}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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