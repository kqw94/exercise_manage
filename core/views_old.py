# core/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models.fields import IntegerField  
from django.db.models import Q, Func
from django.db import models 
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.contrib.auth.models import Group
from .models import User, RolePermission, UserActionLog, Role
from .models import (
    Category, Major, Chapter, ExamGroup, Exercise, ExerciseAnswer, ExerciseAnalysis, Question, ExerciseStem,
    ExerciseType, Source, ExerciseFrom, Exam, School
)
from .serializers import (
    CategorySerializer, MajorSerializer, ChapterSerializer, ExamGroupSerializer,
    ExerciseSerializer, ExerciseAnswerSerializer, ExerciseAnalysisSerializer, QuestionSerializer,
    ExerciseTypeSerializer, SourceSerializer, BulkExerciseUpdateSerializer, ExamSerializer,
    SchoolSerializer, UserRegisterSerializer, UserLoginSerializer, UserSerializer,
    RoleSerializer, RolePermissionSerializer, UserActionLogSerializer
)

import json
import logging
logger = logging.getLogger(__name__)

def log_user_action(request, action_type, model_name=None, object_id=None, details=None):
    """记录用户操作日志"""
    ip_address = request.META.get('REMOTE_ADDR')
    user = request.user if request.user.is_authenticated else None
    UserActionLog.objects.create(
        user=user,
        action_type=action_type,
        model_name=model_name,
        object_id=object_id,
        details=json.dumps(details) if details else None,
        ip_address=ip_address
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


# 4. 根据 category/major/chapter/examgroup 获取 exercise 列表（包含 questions），支持搜索
# 复用并扩展 ExerciseList，支持所有筛选条件
class ExerciseList(APIView):
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.request.method == 'PUT':
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def check_role_permission(self, user, model_name, action):
        if user.is_superuser:  # 超级用户拥有所有权限
            return True
        if not user.role:  # 如果用户没有角色
            return False
        perm = RolePermission.objects.filter(role=user.role, model_name=model_name).first()
        if not perm:
            return False
        if action == 'create':
            return perm.can_create
        elif action == 'read':
            return perm.can_read
        elif action == 'update':
            return perm.can_update
        elif action == 'delete':
            return perm.can_delete
        return False

    def get(self, request):
        if not self.check_role_permission(request.user, 'Exercise', 'read'):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        # 获取查询参数
        category_id = request.query_params.get('category_id')
        major_id = request.query_params.get('major_id')
        chapter_id = request.query_params.get('chapter_id')
        examgroup_id = request.query_params.get('examgroup_id')
        exercise_type = request.query_params.get('exercise_type')
        source = request.query_params.get('source')
        level = request.query_params.get('level')
        score_min = request.query_params.get('score_min')
        score_max = request.query_params.get('score_max')
        search = request.query_params.get('search')
        search_type = request.query_params.get('search_type', 'id')
        order_by = request.query_params.get('order_by', 'id')
        exam_id = request.query_params.get('exam_id')
        exam_school = request.query_params.get('exam_school')
        exam_time = request.query_params.get('exam_time')
        exam_code = request.query_params.get('exam_code')
        exam_full_name = request.query_params.get('exam_full_name')

        # 基础查询集
        exercises = Exercise.objects.all().prefetch_related('questions', 'answer', 'analysis', 'stem', 'exercise_from__exam')

        # 层级筛选
        if category_id:
            exercises = exercises.filter(category_id=category_id)
        if major_id:
            exercises = exercises.filter(major_id=major_id)
        if chapter_id:
            exercises = exercises.filter(chapter_id=chapter_id)
        if examgroup_id:
            exercises = exercises.filter(exam_group_id=examgroup_id)

        # 属性筛选
        if exercise_type:
            exercises = exercises.filter(exercise_type_id=exercise_type)
        if source:
            exercises = exercises.filter(source_id=source)
        if level:
            exercises = exercises.filter(level=level)
        if score_min:
            exercises = exercises.filter(score__gte=score_min)
        if score_max:
            exercises = exercises.filter(score__lte=score_max)

        # 按 Exam 字段筛选
        if exam_id:
            exercises = exercises.filter(exercise_from__exam__exam_id=exam_id)
        if exam_school:
            exercises = exercises.filter(exercise_from__exam__from_school__icontains=exam_school)
        if exam_time:
            exercises = exercises.filter(exercise_from__exam__exam_time__icontains=exam_time)
        if exam_code:
            exercises = exercises.filter(exercise_from__exam__exam_code__icontains=exam_code)
        if exam_full_name:
            exercises = exercises.filter(exercise_from__exam__exam_full_name__icontains=exam_full_name)

        # 搜索逻辑
        if search:
            if search_type == 'id':
                exercises = exercises.filter(exercise_id=search)
            elif search_type == 'content':
                exercises = exercises.filter(
                    Q(stem__stem_content__icontains=search) |
                    Q(questions__question_answer__icontains=search) |
                    Q(answer__answer_content__icontains=search) |
                    Q(analysis__analysis_content__icontains=search)
                ).distinct()

        # 排序逻辑
        valid_order_fields = {
            'id': 'exercise_id',
            'level': 'level',
            'score': 'score',
            'exam.exercise_number': 'exam_exercise_number'
        }
        order_field = valid_order_fields.get(order_by, 'exercise_id')
        
        if order_field == 'exercise_id':
            class Cast(Func):
                function = 'CAST'
                template = '%(function)s(%(expressions)s AS UNSIGNED)'
            exercises = exercises.annotate(id_int=Cast('exercise_id', output_field=IntegerField())).order_by('id_int')
        else:
            exercises = exercises.order_by(order_field)

        # 分页
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(exercises, request)
        serializer = ExerciseSerializer(page, many=True)
        # log_user_action(request, 'read', 'Exercise')
        return paginator.get_paginated_response(serializer.data)

    def put(self, request, exercise_id=None):
        if not self.check_role_permission(request.user, 'Exercise', 'update'):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        logger.debug(f"Received PUT request data: {request.data}")
        try:
            exercise = Exercise.objects.get(exercise_id=exercise_id)
            data = request.data

            if 'stem' in data:
                if exercise.stem:
                    exercise.stem.stem_content = data['stem']
                    exercise.stem.save()
                else:
                    stem = ExerciseStem.objects.create(stem_content=data['stem'])
                    exercise.stem = stem

            if 'answer' in data:
                answer_data = data['answer']
                if exercise.answer:
                    exercise.answer.answer_content = answer_data.get('answer_content', exercise.answer.answer_content)
                    exercise.answer.render_type = answer_data.get('render_type', exercise.answer.render_type)
                    exercise.answer.from_model = answer_data.get('from_model', exercise.answer.from_model)
                    exercise.answer.save()
                else:
                    exercise.answer = ExerciseAnswer.objects.create(**answer_data)

            if 'analysis' in data:
                analysis_data = data['analysis']
                if exercise.analysis:
                    exercise.analysis.analysis_content = analysis_data.get('analysis_content', exercise.analysis.analysis_content)
                    exercise.analysis.render_type = analysis_data.get('render_type', exercise.analysis.render_type)
                    exercise.analysis.save()
                else:
                    exercise.analysis = ExerciseAnalysis.objects.create(**analysis_data)

            if 'questions' in data:
                questions_data = data['questions']
                logger.debug(f"Questions data: {questions_data}")
                for q_data in questions_data:
                    try:
                        question = Question.objects.get(
                            exercise=exercise,
                            question_order=q_data['question_order']
                        )
                        if 'question_answer' in q_data:
                            question.question_answer = q_data['question_answer']
                            question.save()
                            logger.debug(f"Updated question {question.question_order}: {question.question_answer}")
                    except Question.DoesNotExist:
                        logger.warning(f"Question with order {q_data['question_order']} not found for exercise {exercise_id}")
                        Question.objects.create(
                            exercise=exercise,
                            question_order=q_data['question_order'],
                            question_stem=q_data.get('question_stem', ''),
                            question_answer=q_data.get('question_answer', ''),
                            question_analysis=q_data.get('question_analysis', None)
                        )

            exercise.save()
            serializer = ExerciseSerializer(exercise)
            # log_user_action(request, 'update', 'Exercise', exercise_id, request.data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exercise.DoesNotExist:
            return Response({"error": "Exercise not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating exercise {exercise_id}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# 新增：题型列表
class ExerciseTypeList(APIView):
    def get(self, request):
        exercise_types = ExerciseType.objects.all()
        serializer = ExerciseTypeSerializer(exercise_types, many=True)
        return Response(serializer.data)

# 新增：来源列表
class SourceList(APIView):
    def get(self, request):
        sources = Source.objects.all()
        serializer = SourceSerializer(sources, many=True)
        return Response(serializer.data)

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
        

class BulkExerciseUpdate(APIView):
    permission_classes = [IsAuthenticated]  # 要求用户认证

    def check_role_permission(self, user, model_name, action):
        """检查用户是否有指定模型的权限"""
        if user.is_superuser:  # 超级用户拥有所有权限
            return True
        if not user.role:  # 如果用户没有角色
            return False
        perm = RolePermission.objects.filter(role=user.role, model_name=model_name).first()
        if not perm:
            return False
        if action == 'create':
            return perm.can_create
        elif action == 'read':
            return perm.can_read
        elif action == 'update':
            return perm.can_update
        elif action == 'delete':
            return perm.can_delete
        return False

    def post(self, request):
        # 检查更新权限
        if not self.check_role_permission(request.user, 'Exercise', 'update'):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        logger.info(f"Received bulk update request: {request.data}")
        serializer = BulkExerciseUpdateSerializer(data=request.data)
        if serializer.is_valid():
            exercise_ids = serializer.validated_data['exercise_ids']
            update_data = {}
            if 'exam_group' in serializer.validated_data:
                update_data['exam_group_id'] = serializer.validated_data['exam_group']
            if 'level' in serializer.validated_data:
                update_data['level'] = serializer.validated_data['level']
            if 'score' in serializer.validated_data:
                update_data['score'] = serializer.validated_data['score']

            try:
                updated_count = Exercise.objects.filter(exercise_id__in=exercise_ids).update(**update_data)
                # log_user_action(request, 'update', 'Exercise', exercise_ids)  # 可选：记录日志
                return Response({
                    "message": f"Successfully updated {updated_count} exercises",
                    "updated_ids": exercise_ids
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error in bulk update: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# School CRUD 接口
class SchoolList(APIView):
    pagination_class = StandardPagination

    def get(self, request):
        """获取学校列表（带分页）"""
        schools = School.objects.all()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(schools, request)
        serializer = SchoolSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        """创建新学校"""
        serializer = SchoolSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SchoolDetail(APIView):
    def get_object(self, pk):
        """辅助方法：获取学校对象"""
        try:
            return School.objects.get(pk=pk)
        except School.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND

    def get(self, request, pk):
        """获取单个学校详情"""
        school = self.get_object(pk)
        serializer = SchoolSerializer(school)
        return Response(serializer.data)

    def put(self, request, pk):
        """更新学校"""
        school = self.get_object(pk)
        serializer = SchoolSerializer(school, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """删除学校"""
        school = self.get_object(pk)
        school.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ExamList(APIView):
    pagination_class = StandardPagination

    def get(self, request):
        exams = Exam.objects.all()
        # 支持单一或联合搜索
        school_id = request.query_params.get('school_id')
        exam_school = request.query_params.get('exam_school')
        exam_time = request.query_params.get('exam_time')
        exam_code = request.query_params.get('exam_code')
        exam_full_name = request.query_params.get('exam_full_name')
        category_id = request.query_params.get('category_id')  # 新增支持按 category 过滤


        if school_id:
            exams = exams.filter(school_id=school_id)
        if category_id:
            exams = exams.filter(category_id=category_id)
        if exam_school:
            exams = exams.filter(from_school__icontains=exam_school)
        if exam_time:
            exams = exams.filter(exam_time__icontains=exam_time)
        if exam_code:
            exams = exams.filter(exam_code__icontains=exam_code)
        if exam_full_name:
            exams = exams.filter(exam_full_name__icontains=exam_full_name)
        

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(exams, request)
        serializer = ExamSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        """创建新试卷"""
        serializer = ExamSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ExamDetail(APIView):
    def get_object(self, pk):
        """辅助方法：获取试卷对象"""
        try:
            return Exam.objects.get(pk=pk)
        except Exam.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND

    def get(self, request, pk):
        """获取单个试卷详情"""
        exam = self.get_object(pk)
        serializer = ExamSerializer(exam)
        return Response(serializer.data)

    def put(self, request, pk):
        """更新试卷"""
        exam = self.get_object(pk)
        serializer = ExamSerializer(exam, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """删除试卷"""
        exam = self.get_object(pk)
        exam.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ExamSchoolListByCategoryId(APIView):
    """
    获取根据 category_id 过滤的唯一 from_school 列表
    """
    pagination_class = StandardPagination

    def get(self, request):
        # 获取查询参数
        category_id = request.query_params.get('category_id', None)

        # 构建查询条件
        queryset = Exam.objects.all()
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # 获取唯一的 from_school 并排序
        schools = queryset.values('from_school').distinct()
        school_list = [{'name': school['from_school']} for school in schools if school['from_school']]

        # 分页处理（可选）
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(school_list, request)
        return paginator.get_paginated_response(page) if page is not None else Response(school_list)


    # 新增：获取所有唯一的 exam_school
class ExamSchoolList(APIView):
    def get(self, request):
        exam_schools = Exam.objects.values('from_school').distinct().exclude(from_school__isnull=True).exclude(from_school='')
        schools = [{'name': school['from_school']} for school in exam_schools]
        return Response(schools)

# 新增：根据 exam_school 获取 exam_time
class ExamTimeList(APIView):
    def get(self, request, exam_school):
        exam_times = Exam.objects.filter(from_school=exam_school).values('exam_time').distinct().exclude(exam_time__isnull=True).exclude(exam_time='')
        times = [{'name': time['exam_time']} for time in exam_times]
        return Response(times)

# 新增：根据 exam_school 和 exam_time 获取 exam_code
class ExamCodeList(APIView):
    def get(self, request, exam_school, exam_time):
        exam_codes = Exam.objects.filter(from_school=exam_school, exam_time=exam_time).values('exam_code').distinct().exclude(exam_code__isnull=True).exclude(exam_code='')
        codes = [{'name': code['exam_code']} for code in exam_codes]
        return Response(codes)

# 新增：根据 exam_school、exam_time 和 exam_code 获取 exam_full_name
class ExamFullNameList(APIView):
    def get(self, request, exam_school, exam_time, exam_code):
        exam_full_names = Exam.objects.filter(
            from_school=exam_school, 
            exam_time=exam_time, 
            exam_code=exam_code
        ).values('exam_full_name').distinct().exclude(exam_full_name__isnull=True).exclude(exam_full_name='')
        full_names = [{'name': name['exam_full_name']} for name in exam_full_names]
        return Response(full_names)
    



# --- 新增 CRUD 接口 ---

# Category CRUD
class CategoryCreate(APIView):
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoryDetail(APIView):
    def get(self, request, category_id):
        try:
            category = Category.objects.get(category_id=category_id)
            serializer = CategorySerializer(category)
            return Response(serializer.data)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, category_id):
        try:
            category = Category.objects.get(category_id=category_id)
            serializer = CategorySerializer(category, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, category_id):
        try:
            category = Category.objects.get(category_id=category_id)
            category.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

# Major CRUD
class MajorCreate(APIView):
    def post(self, request):
        serializer = MajorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MajorDetail(APIView):
    def get(self, request, major_id):
        try:
            major = Major.objects.get(major_id=major_id)
            serializer = MajorSerializer(major)
            return Response(serializer.data)
        except Major.DoesNotExist:
            return Response({"error": "Major not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, major_id):
        try:
            major = Major.objects.get(major_id=major_id)
            serializer = MajorSerializer(major, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Major.DoesNotExist:
            return Response({"error": "Major not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, major_id):
        try:
            major = Major.objects.get(major_id=major_id)
            major.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Major.DoesNotExist:
            return Response({"error": "Major not found"}, status=status.HTTP_404_NOT_FOUND)

# Chapter CRUD
class ChapterCreate(APIView):
    def post(self, request):
        serializer = ChapterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChapterDetail(APIView):
    def get(self, request, chapter_id):
        try:
            chapter = Chapter.objects.get(chapter_id=chapter_id)
            serializer = ChapterSerializer(chapter)
            return Response(serializer.data)
        except Chapter.DoesNotExist:
            return Response({"error": "Chapter not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, chapter_id):
        try:
            chapter = Chapter.objects.get(chapter_id=chapter_id)
            serializer = ChapterSerializer(chapter, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Chapter.DoesNotExist:
            return Response({"error": "Chapter not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, chapter_id):
        try:
            chapter = Chapter.objects.get(chapter_id=chapter_id)
            chapter.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Chapter.DoesNotExist:
            return Response({"error": "Chapter not found"}, status=status.HTTP_404_NOT_FOUND)

# ExamGroup CRUD
class ExamGroupCreate(APIView):
    def post(self, request):
        serializer = ExamGroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ExamGroupDetail(APIView):
    def get(self, request, examgroup_id):
        try:
            examgroup = ExamGroup.objects.get(examgroup_id=examgroup_id)
            serializer = ExamGroupSerializer(examgroup)
            return Response(serializer.data)
        except ExamGroup.DoesNotExist:
            return Response({"error": "ExamGroup not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, examgroup_id):
        try:
            examgroup = ExamGroup.objects.get(examgroup_id=examgroup_id)
            serializer = ExamGroupSerializer(examgroup, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ExamGroup.DoesNotExist:
            return Response({"error": "ExamGroup not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, examgroup_id):
        try:
            examgroup = ExamGroup.objects.get(examgroup_id=examgroup_id)
            examgroup.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ExamGroup.DoesNotExist:
            return Response({"error": "ExamGroup not found"}, status=status.HTTP_404_NOT_FOUND)



# --- 1. 登录注册接口 ---

class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            log_user_action(request, 'create', 'User', str(user.id), {'username': user.username})
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            login(request, user)
            refresh = RefreshToken.for_user(user)
            # log_user_action(request, 'login', 'User', str(user.id))
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = str(request.user.id)
        logout(request)
        # log_user_action(request, 'logout', 'User', user_id)
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)

# --- 2. 用户管理接口 ---

class UserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = StandardPagination

    def get(self, request):
        users = User.objects.all()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(users, request)
        serializer = UserSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # 处理角色
            if 'role' in request.data:
                group, _ = Group.objects.get_or_create(name=request.data['role'])
                user.groups.clear()
                user.groups.add(group)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                user = serializer.save()
                # 更新角色
                if 'role' in request.data:
                    role = Role.objects.get(id=request.data['role'])
                    user.role = role
                    user.save()  # 触发 save 方法，同步更新 groups
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_400_BAD_REQUEST)
        

# --- 3. 角色管理接口 ---

class RoleListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = StandardPagination

    def get(self, request):
        roles = Role.objects.all()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(roles, request)
        serializer = RoleSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            role = serializer.save()
            # 同步创建 Group（由 Role 的 save 方法自动处理）
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RoleDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
            serializer = RoleSerializer(role)
            return Response(serializer.data)
        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
            serializer = RoleSerializer(role, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
            role.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)

# --- 角色权限管理 ---

class RolePermissionListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = StandardPagination

    def get(self, request):
        permissions = RolePermission.objects.all()
        role_id = request.query_params.get('role')
        if role_id:
            permissions = permissions.filter(role_id=role_id)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(permissions, request)
        serializer = RolePermissionSerializer(page, many=True)
        return Response(serializer.data)  # 返回完整列表，不分页

    def post(self, request):
        serializer = RolePermissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RolePermissionDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, pk):
        try:
            permission = RolePermission.objects.get(pk=pk)
            serializer = RolePermissionSerializer(permission)
            return Response(serializer.data)
        except RolePermission.DoesNotExist:
            return Response({"error": "Permission not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            permission = RolePermission.objects.get(pk=pk)
            serializer = RolePermissionSerializer(permission, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except RolePermission.DoesNotExist:
            return Response({"error": "Permission not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            permission = RolePermission.objects.get(pk=pk)
            permission.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except RolePermission.DoesNotExist:
            return Response({"error": "Permission not found"}, status=status.HTTP_404_NOT_FOUND)



class UserActionLogListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = StandardPagination

    def get(self, request):
        """获取操作日志列表"""
        logs = UserActionLog.objects.all().order_by('-timestamp')
        
        # 筛选参数
        user_id = request.query_params.get('user_id')
        action_type = request.query_params.get('action_type')
        model_name = request.query_params.get('model_name')
        
        if user_id:
            logs = logs.filter(user_id=user_id)
        if action_type:
            logs = logs.filter(action_type=action_type)
        if model_name:
            logs = logs.filter(model_name=model_name)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(logs, request)
        serializer = UserActionLogSerializer(page, many=True)
        return Response(paginator.get_paginated_response(serializer.data))


class UserActionLogDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, pk):
        """获取单条操作日志详情"""
        try:
            log = UserActionLog.objects.get(pk=pk)
            serializer = UserActionLogSerializer(log)
            return Response(serializer.data)
        except UserActionLog.DoesNotExist:
            return Response({"error": "Log not found"}, status=status.HTTP_404_NOT_FOUND)
        

class InitializeRolesView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        # 定义角色和权限
        roles_permissions = {
            'user': [
                {'model_name': 'Exercise', 'can_create': False, 'can_read': True, 'can_update': False, 'can_delete': False},
                {'model_name': 'Category', 'can_create': False, 'can_read': True, 'can_update': False, 'can_delete': False},
                # 添加其他模型...
            ],
            'editor': [
                {'model_name': 'Exercise', 'can_create': True, 'can_read': True, 'can_update': True, 'can_delete': False},
                {'model_name': 'Category', 'can_create': True, 'can_read': True, 'can_update': True, 'can_delete': False},
                # 添加其他模型...
            ],
        }

        for role_name, permissions in roles_permissions.items():
            group, created = Group.objects.get_or_create(name=role_name)
            for perm in permissions:
                RolePermission.objects.update_or_create(
                    role=group,
                    model_name=perm['model_name'],
                    defaults={
                        'can_create': perm['can_create'],
                        'can_read': perm['can_read'],
                        'can_update': perm['can_update'],
                        'can_delete': perm['can_delete'],
                    }
                )
        
        return Response({"message": "Roles and permissions initialized successfully"}, status=status.HTTP_200_OK)