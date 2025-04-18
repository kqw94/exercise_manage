# core/views.py
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from django.db.models.fields import IntegerField  
from django.db.models import Q, Func
from django.db import models, transaction 
from django.core.files.uploadedfile import UploadedFile
from django.http import JsonResponse, FileResponse, StreamingHttpResponse

import json
import os
import traceback
from datetime import datetime
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.contrib.auth.models import Group
from django.db.models.functions import Cast
from django.core.serializers.json import DjangoJSONEncoder
from .models import User, RolePermission, UserActionLog, Role
from .models import (
    Category, Major, Chapter, ExamGroup, Exercise, ExerciseAnswer, ExerciseAnalysis, Question, ExerciseStem,
    ExerciseType, Source, ExerciseFrom, Exam, School, ExerciseImage
)
from .serializers import (
    CategorySerializer, MajorSerializer, ChapterSerializer, ExamGroupSerializer,
    ExerciseSerializer, ExerciseAnswerSerializer, ExerciseAnalysisSerializer, QuestionSerializer,
    ExerciseTypeSerializer, SourceSerializer, BulkExerciseUpdateSerializer, ExamSerializer,
    SchoolSerializer, UserRegisterSerializer, UserLoginSerializer, UserSerializer,
    RoleSerializer, RolePermissionSerializer, UserActionLogSerializer, BulkExerciseSerializer,
    ExerciseWriteSerializer
)
from functools import wraps
from django.http import JsonResponse
from uuid import uuid4

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
        details=json.dumps(details, ensure_ascii=False) if details else None,
        ip_address=ip_address
    )

def require_permission(model_name, action):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            user = request.user
            if user.is_superuser:
                return view_func(self, request, *args, **kwargs)
            if not user.role:
                return JsonResponse({"error": "No role assigned"}, status=status.HTTP_403_FORBIDDEN)
            perm = RolePermission.objects.filter(role=user.role, model_name=model_name).first()
            if not perm or not getattr(perm, f"can_{action}", False):
                return JsonResponse({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
            return view_func(self, request, *args, **kwargs)
        return _wrapped_view
    return decorator



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

    #@require_permission('Major', 'read')
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

    #@require_permission('Chapter', 'read')
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

    #@require_permission('ExamGroup', 'read')
    def get(self, request, chapter_id):
        try:
            exam_groups = ExamGroup.objects.filter(chapter_id=chapter_id)
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(exam_groups, request)
            serializer = ExamGroupSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Chapter.DoesNotExist:
            return Response({"error": "Chapter not found"}, status=status.HTTP_404_NOT_FOUND)




# 复用并扩展 ExerciseList，支持所有筛选条件
class ExerciseList(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

   
    #@require_permission('Exercise', 'read')
    def get(self, request):
        
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
        # exercises = Exercise.objects.select_related(
        #     'category', 'major', 'chapter', 'exam_group', 'source', 'exercise_type',
        #     'stem', 'answer', 'analysis', 'exercise_from', 'exercise_from__exam'
        #     ).prefetch_related('questions', 'answers', 'analyses')

        exercises = Exercise.objects.select_related(
                'category', 'major', 'chapter', 'exam_group', 'source', 'exercise_type', 
                ).prefetch_related('questions')

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
        
        
        exercises = exercises.order_by(order_field)

        # 分页
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(exercises, request)
        serializer = ExerciseSerializer(page, many=True)
        # log_user_action(request, 'read', 'Exercise')
        return paginator.get_paginated_response(serializer.data)

    @require_permission('Exercise', 'update')
    def put(self, request, exercise_id=None):
        
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
                        logger.warning(f"Question with order {q_data['question_order']} not found for exercise {str(exercise_id)}")
                        Question.objects.create(
                            exercise=exercise,
                            question_order=q_data['question_order'],
                            question_stem=q_data.get('question_stem', ''),
                            question_answer=q_data.get('question_answer', ''),
                            question_analysis=q_data.get('question_analysis', None)
                        )

            exercise.save()
            serializer = ExerciseSerializer(exercise)
            details = request.data.get('details', [])
            log_user_action(request, 'update', 'Exercise', exercise_id, details=request.data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exercise.DoesNotExist:
            return Response({"error": "Exercise not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating exercise {str(exercise_id)}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @require_permission('Exercise', 'create')
    def post(self, request):
        """添加 Exercise"""
        
        serializer = ExerciseSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    exercise = serializer.save()
                    logger.info(f"Exercise {exercise.exercise_id} created by user {request.user.username}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error creating exercise: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @require_permission('Exercise', 'delete')
    def delete(self, request, exercise_id=None):
        """删除 Exercise"""
       
        if not exercise_id:
            return Response({"error": "缺少 exercise_id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            exercise = Exercise.objects.get(exercise_id=exercise_id)
            with transaction.atomic():
                exercise.delete()
                logger.info(f"Exercise {exercise_id} deleted by user {request.user.username}")
            log_user_action(request=request, action_type='delete', model_name='Exercise', object_id=exercise_id)
            return Response({"message": f"成功删除练习题 {exercise_id}"}, status=status.HTTP_200_OK)
        except Exercise.DoesNotExist:
            return Response({"error": "练习题不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting exercise {exercise_id}: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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



class BulkExerciseCreateView(APIView):
    # permission_classes = [IsAuthenticated]

    

    def post(self, request):
        
        serializer = BulkExerciseSerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                exercises = serializer.save()
                logger.info(f"Imported {len(exercises)} exercises by user {request.user.username}")
                return Response({"message": f"成功导入 {len(exercises)} 道练习题"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error importing exercises: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class BulkExerciseUpdate(APIView):
    
    #@require_permission('Exercise', 'update')
    def post(self, request):
        
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

    #@require_permission('School', 'read')
    def get(self, request):
        """获取学校列表（带分页）"""
        schools = School.objects.all()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(schools, request)
        serializer = SchoolSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @require_permission('School', 'create')
    def post(self, request):
        """创建新学校"""
        serializer = SchoolSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            log_user_action(request, 'create', 'School', details=request.data)
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

    @require_permission('School', 'update')
    def put(self, request, pk):
        """更新学校"""
        school = self.get_object(pk)
        serializer = SchoolSerializer(school, data=request.data)
        if serializer.is_valid():
            serializer.save()
            log_user_action(request, 'update', 'School', pk)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @require_permission('School', 'delete')
    def delete(self, request, pk):
        """删除学校"""
        school = self.get_object(pk)
        school.delete()
        log_user_action(request, 'delete', 'School', pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ExamList(APIView):
    pagination_class = StandardPagination

    #@require_permission('Exam', 'read')
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

    @require_permission('Exam', 'create')
    def post(self, request):
        """创建新试卷"""
        serializer = ExamSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            log_user_action(request, 'create', 'Exam', details=request.data)
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

    @require_permission('Exam', 'update')
    def put(self, request, pk):
        """更新试卷"""
        exam = self.get_object(pk)
        serializer = ExamSerializer(exam, data=request.data)
        if serializer.is_valid():
            serializer.save()
            log_user_action(request, 'update', 'Exam', pk, request.data)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @require_permission('Exam', 'delete')
    def delete(self, request, pk):
        """删除试卷"""
        exam = self.get_object(pk)
        exam.delete()
        log_user_action(request, 'delete', 'Exam', pk)
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

    @require_permission('Category', 'create')
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            log_user_action(request, 'create', 'Category', details=request.data)
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

    @require_permission('Category', 'update')
    def put(self, request, category_id):
        try:
            category = Category.objects.get(category_id=category_id)
            serializer = CategorySerializer(category, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                log_user_action(request, 'update', 'category', category_id, request.data)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

    @require_permission('Category', 'delete')
    def delete(self, request, category_id):
        try:
            category = Category.objects.get(category_id=category_id)
            category.delete()
            log_user_action(request, 'delete', 'Category', category_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

# Major CRUD
class MajorCreate(APIView):
    @require_permission('Major', 'create')
    def post(self, request):
        serializer = MajorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            log_user_action(request, 'create', 'Major', details=request.data)
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

    @require_permission('Major', 'update')
    def put(self, request, major_id):
        try:
            major = Major.objects.get(major_id=major_id)
            serializer = MajorSerializer(major, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                log_user_action(request, 'update', 'Major', major_id, details=request.data)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Major.DoesNotExist:
            return Response({"error": "Major not found"}, status=status.HTTP_404_NOT_FOUND)

    @require_permission('Major', 'delete')
    def delete(self, request, major_id):
        try:
            major = Major.objects.get(major_id=major_id)
            major.delete()
            log_user_action(request, 'delete', 'Major', major_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Major.DoesNotExist:
            return Response({"error": "Major not found"}, status=status.HTTP_404_NOT_FOUND)

# Chapter CRUD
class ChapterCreate(APIView):
    @require_permission('Chapter', 'create')
    def post(self, request):
        serializer = ChapterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            log_user_action(request, 'create', 'Chapter')
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

    @require_permission('Chapter', 'update')
    def put(self, request, chapter_id):
        try:
            chapter = Chapter.objects.get(chapter_id=chapter_id)
            serializer = ChapterSerializer(chapter, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                log_user_action(request, 'update', 'Chapter', chapter_id, details=request.data)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Chapter.DoesNotExist:
            return Response({"error": "Chapter not found"}, status=status.HTTP_404_NOT_FOUND)

    @require_permission('Chapter', 'delete')
    def delete(self, request, chapter_id):
        try:
            chapter = Chapter.objects.get(chapter_id=chapter_id)
            chapter.delete()
            log_user_action(request, 'delete', 'Chapter', chapter_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Chapter.DoesNotExist:
            return Response({"error": "Chapter not found"}, status=status.HTTP_404_NOT_FOUND)

# ExamGroup CRUD
class ExamGroupCreate(APIView):
    @require_permission('ExamGroup', 'create')
    def post(self, request):
        serializer = ExamGroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            log_user_action(request, 'create', 'ExamGroup')
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

    @require_permission('ExamGroup', 'update')
    def put(self, request, examgroup_id):
        try:
            examgroup = ExamGroup.objects.get(examgroup_id=examgroup_id)
            serializer = ExamGroupSerializer(examgroup, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                log_user_action(request, 'update', 'ExamGroup', examgroup_id, details=request.data)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ExamGroup.DoesNotExist:
            return Response({"error": "ExamGroup not found"}, status=status.HTTP_404_NOT_FOUND)

    @require_permission('ExamGroup', 'delete')
    def delete(self, request, examgroup_id):
        try:
            examgroup = ExamGroup.objects.get(examgroup_id=examgroup_id)
            examgroup.delete()
            log_user_action(request, 'delete', 'ExmaGroup', examgroup_id)
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
            # 移除基于会话的登录
            # login(request, user)
            refresh = RefreshToken.for_user(user)
            log_user_action(request, 'login', 'User', str(user.id))
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
    


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # 从请求数据中获取刷新令牌
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({"error": "需要提供刷新令牌"}, status=status.HTTP_400_BAD_REQUEST)

            # 将刷新令牌列入黑名单
            token = RefreshToken(refresh_token)
            token.blacklist()

            # 记录操作
            user_id = str(request.user.id)
            log_user_action(request, 'logout', 'User', user_id)
            return Response({"message": "登出成功"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"登出错误: {str(e)}")
            return Response({"error": "无效或已过期的令牌"}, status=status.HTTP_400_BAD_REQUEST)

class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"error": "需要提供刷新令牌"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            access_token = str(token.access_token)
            return Response({
                'access': access_token,
                'refresh': str(token)  # 可选：返回新的刷新令牌
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"令牌刷新错误: {str(e)}")
            return Response({"error": "无效或已过期的刷新令牌"}, status=status.HTTP_401_UNAUTHORIZED)



# --- 2. 用户管理接口 ---

class UserListView(APIView):
    # permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = StandardPagination

    @require_permission('User', 'read')
    def get(self, request):
        users = User.objects.all()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(users, request)
        serializer = UserSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @require_permission('User', 'create')
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # 处理角色
            if 'role' in request.data:
                group, _ = Group.objects.get_or_create(name=request.data['role'])
                user.groups.clear()
                user.groups.add(group)
            log_user_action(request, 'create', 'Role', details=request.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    # permission_classes = [IsAuthenticated, IsAdminUser]

    @require_permission('User', 'update')
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
                log_user_action(request, 'update', 'User', pk, request.data)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_400_BAD_REQUEST)
        

# --- 3. 角色管理接口 ---

class RoleListView(APIView):
    # permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = StandardPagination

    @require_permission('Role', 'read')
    def get(self, request):
        roles = Role.objects.all()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(roles, request)
        serializer = RoleSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @require_permission('Role', 'create')
    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            role = serializer.save()
            # 同步创建 Group（由 Role 的 save 方法自动处理）
            log_user_action(request, 'create', 'Role', details=request.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RoleDetailView(APIView):
    # permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
            serializer = RoleSerializer(role)
            return Response(serializer.data)
        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)

    @require_permission('Role', 'update')
    def put(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
            serializer = RoleSerializer(role, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                log_user_action(request, 'update', 'Role',  pk, details=request.data)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)

    @require_permission('Role', 'delete')
    def delete(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
            role.delete()
            log_user_action(request, 'delete', 'Role', pk)
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
            log_user_action(request, 'create', 'RolePermission', details=request.data)
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
                log_user_action(request, 'update', 'RolePermission', pk, request.data)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except RolePermission.DoesNotExist:
            return Response({"error": "Permission not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            permission = RolePermission.objects.get(pk=pk)
            permission.delete()
            log_user_action(request, 'delete', 'RolePermission', pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except RolePermission.DoesNotExist:
            return Response({"error": "Permission not found"}, status=status.HTTP_404_NOT_FOUND)







class InitializeRolesView(APIView):
    # permission_classes = [IsAuthenticated, IsAdminUser]

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
    

class ExportExercisesByCategoryView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def generate_json_stream(self, exercises):
        """生成器函数，流式生成 JSON 数据"""
        logger.info("Starting JSON stream generation")
        yield '['
        first = True
        exercise_count = 0

        for exercise in exercises:
            try:
                exercise_count += 1
                logger.debug(f"Processing exercise: {exercise.exercise_id}")
                if not first:
                    yield ','
                first = False

                exercise_data = {
                    "exercise_id": exercise.exercise_id,
                    "category": exercise.category.category_name if exercise.category else None,
                    "major": exercise.major.major_name if exercise.major else None,
                    "chapter": exercise.chapter.chapter_name if exercise.chapter else None,
                    "examgroup": exercise.exam_group.examgroup_name if exercise.exam_group else None,
                    "source": exercise.source.source_name if exercise.source else None,
                    "type": exercise.exercise_type.type_name if exercise.exercise_type else None,
                    "level": exercise.level,
                    "score": exercise.score,
                    "stem": exercise.stem.stem_content if exercise.stem else None,
                    "questions": [
                        {
                            "question_order": q.question_order,
                            "question_stem": q.question_stem,
                            "question_answer": q.question_answer,
                            "question_analysis": q.question_analysis
                        } for q in exercise.questions.all()
                    ],
                    "answer": [
                        {
                            "answer_content": a.answer_content,
                            "mark": a.mark,
                            "from_model": a.from_model,
                            "render_type": a.render_type
                        } for a in exercise.answers.all()
                    ],
                    "analysis": [
                        {
                            "analysis_content": a.analysis_content,
                            "mark": a.mark,
                            "render_type": a.render_type
                        } for a in exercise.analyses.all()
                    ],
                    "exercise_from": {
                        "is_official_exercise": exercise.exercise_from.is_official_exercise if exercise.exercise_from else 0,
                        "from_school": exercise.exercise_from.exam.from_school if exercise.exercise_from and exercise.exercise_from.exam else "",
                        "exam_time": exercise.exercise_from.exam.exam_time if exercise.exercise_from and exercise.exercise_from.exam else "",
                        "exam_code": exercise.exercise_from.exam.exam_code if exercise.exercise_from and exercise.exercise_from.exam else "",
                        "exam_full_name": exercise.exercise_from.exam.exam_full_name if exercise.exercise_from and exercise.exercise_from.exam else "",
                        "exercise_number": exercise.exercise_from.exercise_number if exercise.exercise_from else 0,
                        "material_name": exercise.exercise_from.material_name if exercise.exercise_from else "",
                        "section": exercise.exercise_from.section if exercise.exercise_from else "",
                        "page_number": exercise.exercise_from.page_number if exercise.exercise_from else 0
                    },
                    "image_links": [
                        {
                            "image_link": img.image_link,
                            "source_type": img.source_type,
                            "is_deprecated": img.is_deprecated,
                            "ocr_result": img.ocr_result
                        } for img in exercise.exercise_images.all()
                    ]
                }
                yield json.dumps(exercise_data, ensure_ascii=False, cls=DjangoJSONEncoder)
            except Exception as e:
                logger.error(f"Error processing exercise {exercise.exercise_id}: {str(e)}")
                continue

        yield ']'
        logger.info(f"Finished generating JSON stream, total exercises: {exercise_count}")

    def get(self, request, category_id):
        
        try:
            category = Category.objects.get(category_id=category_id)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)

        
        exercises = Exercise.objects.filter(category=category).order_by('exercise_id').select_related(
                    'exercise_type', 'category', 'major', 'chapter', 'exam_group', 'source', 'stem', 'answer', 'analysis', 'exercise_from'
                    ).prefetch_related(
                    'questions', 'answers', 'analyses', 'exercise_from__exam', 'exercise_images'
                    ).iterator(chunk_size=500)

        total_exercises = Exercise.objects.filter(category=category).count()
        logger.info(f"Exporting {total_exercises} exercises for category {category_id}")

        response = StreamingHttpResponse(
            self.generate_json_stream(exercises),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="exercises_category_{category_id}.json"'
        log_user_action(request, 'export')
        return response


class ExportExercisesView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def generate_json_stream(self, exercises):
        """生成器函数，流式生成 JSON 数据"""
        logger.info("Starting JSON stream generation")
        yield '['
        batch = []
        batch_size = 10  # 每批次处理 10 条记录
        exercise_count = 0

        for exercise in exercises:
            try:
                exercise_count += 1
                logger.debug(f"Processing exercise: {exercise.exercise_id}")

                exercise_data = {
                    "exercise_id": exercise.exercise_id,
                    "category": exercise.category.category_name if exercise.category else None,
                    "major": exercise.major.major_name if exercise.major else None,
                    "chapter": exercise.chapter.chapter_name if exercise.chapter else None,
                    "examgroup": exercise.exam_group.examgroup_name if exercise.exam_group else None,
                    "source": exercise.source.source_name if exercise.source else None,
                    "type": exercise.exercise_type.type_name if exercise.exercise_type else None,
                    "level": exercise.level,
                    "score": exercise.score,
                    "stem": exercise.stem.stem_content if exercise.stem else None,
                    "questions": [
                        {
                            "question_order": q.question_order,
                            "question_stem": q.question_stem,
                            "question_answer": q.question_answer,
                            "question_analysis": q.question_analysis
                        } for q in exercise.questions.all()
                    ],
                    "answer": [
                        {
                            "answer_content": a.answer_content,
                            "mark": a.mark,
                            "from_model": a.from_model,
                            "render_type": a.render_type
                        } for a in exercise.answers.all()
                    ],
                    "analysis": [
                        {
                            "analysis_content": a.analysis_content,
                            "mark": a.mark,
                            "render_type": a.render_type
                        } for a in exercise.analyses.all()
                    ],
                    "exercise_from": {
                        "is_official_exercise": exercise.exercise_from.is_official_exercise if exercise.exercise_from else 0,
                        "from_school": exercise.exercise_from.exam.from_school if exercise.exercise_from and exercise.exercise_from.exam else "",
                        "exam_time": exercise.exercise_from.exam.exam_time if exercise.exercise_from and exercise.exercise_from.exam else "",
                        "exam_code": exercise.exercise_from.exam.exam_code if exercise.exercise_from and exercise.exercise_from.exam else "",
                        "exam_full_name": exercise.exercise_from.exam.exam_full_name if exercise.exercise_from and exercise.exercise_from.exam else "",
                        "exercise_number": exercise.exercise_from.exercise_number if exercise.exercise_from else 0,
                        "material_name": exercise.exercise_from.material_name if exercise.exercise_from else "",
                        "section": exercise.exercise_from.section if exercise.exercise_from else "",
                        "page_number": exercise.exercise_from.page_number if exercise.exercise_from else 0
                    },
                    "image_links": [
                        {
                            "image_link": img.image_link,
                            "source_type": img.source_type,
                            "is_deprecated": img.is_deprecated,
                            "ocr_result": img.ocr_result
                        } for img in exercise.exercise_images.all()
                    ]
                }
                batch.append(exercise_data)

                if len(batch) >= batch_size:
                    yield json.dumps(batch, ensure_ascii=False, cls=DjangoJSONEncoder)[1:-1]
                    batch = []
                    yield ',' if exercise_count < total_exercises else ''

            except Exception as e:
                logger.error(f"Error processing exercise {exercise.exercise_id}: {str(e)}")
                continue

        if batch:  # 处理剩余的 batch
            yield json.dumps(batch, ensure_ascii=False, cls=DjangoJSONEncoder)[1:-1]
        yield ']'
        logger.info(f"Finished generating JSON stream, total exercises: {exercise_count}")

    def get(self, request):
        # 获取查询参数
        category_id = request.query_params.get('category_id')
        major_id = request.query_params.get('major_id')
        chapter_id = request.query_params.get('chapter_id')
        examgroup_id = request.query_params.get('examgroup_id')
        school_id = request.query_params.get('school_id')
        exam_id = request.query_params.get('exam_id')

        # 构建查询集
        exercises = Exercise.objects.select_related(
            'exercise_type', 'category', 'major', 'chapter', 'exam_group', 'source', 'stem', 'answer', 'analysis', 'exercise_from'
        ).prefetch_related(
            'questions', 'answers', 'analyses', 'exercise_from__exam', 'exercise_images'
        )

        # 应用过滤条件
        filters_applied = False
        if category_id:
            try:
                Category.objects.get(category_id=category_id)
                exercises = exercises.filter(category_id=category_id)
                filters_applied = True
            except Category.DoesNotExist:
                return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if major_id:
            try:
                Major.objects.get(major_id=major_id)
                exercises = exercises.filter(major_id=major_id)
                filters_applied = True
            except Major.DoesNotExist:
                return Response({"error": "Major not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if chapter_id:
            try:
                Chapter.objects.get(chapter_id=chapter_id)
                exercises = exercises.filter(chapter_id=chapter_id)
                filters_applied = True
            except Chapter.DoesNotExist:
                return Response({"error": "Chapter not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if examgroup_id:
            try:
                ExamGroup.objects.get(examgroup_id=examgroup_id)
                exercises = exercises.filter(exam_group_id=examgroup_id)
                filters_applied = True
            except ExamGroup.DoesNotExist:
                return Response({"error": "ExamGroup not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if school_id:
            try:
                School.objects.get(school_id=school_id)
                exercises = exercises.filter(exercise_from__exam__school_id=school_id)
                filters_applied = True
            except School.DoesNotExist:
                return Response({"error": "School not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if exam_id:
            try:
                Exam.objects.get(exam_id=exam_id)
                exercises = exercises.filter(exercise_from__exam_id=exam_id)
                filters_applied = True
            except Exam.DoesNotExist:
                return Response({"error": "Exam not found"}, status=status.HTTP_404_NOT_FOUND)

        # 如果没有任何过滤条件，返回错误
        if not filters_applied:
            return Response({"error": "At least one filter parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 计算总数用于日志
        global total_exercises
        total_exercises = exercises.count()

        # 按 exercise_id 排序并转换为生成器
        exercises = exercises.order_by('exercise_id').iterator(chunk_size=500)

        # 记录日志
        logger.info(f"Exporting {total_exercises} exercises with filters: "
                    f"category_id={category_id}, major_id={major_id}, chapter_id={chapter_id}, "
                    f"examgroup_id={examgroup_id}, school_id={school_id}, exam_id={exam_id}")

        # 动态生成文件名，添加时间戳
        filename_parts = []
        if category_id:
            filename_parts.append(f"category_{category_id}")
        if major_id:
            filename_parts.append(f"major_{major_id}")
        if chapter_id:
            filename_parts.append(f"chapter_{chapter_id}")
        if examgroup_id:
            filename_parts.append(f"examgroup_{examgroup_id}")
        if school_id:
            filename_parts.append(f"school_{school_id}")
        if exam_id:
            filename_parts.append(f"exam_{exam_id}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exercises_{'_'.join(filename_parts)}_{timestamp}.json" if filename_parts else f"exercises_{timestamp}.json"

        # 返回流式响应
        response = StreamingHttpResponse(
            self.generate_json_stream(exercises),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        log_user_action(request, 'export', 'Exercise', details={
            'category_id': category_id,
            'major_id': major_id,
            'chapter_id': chapter_id,
            'examgroup_id': examgroup_id,
            'school_id': school_id,
            'exam_id': exam_id,
            'total_exercises': total_exercises
        })
        return response



class ImportExercisesView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def post(self, request):
        file_obj = request.FILES.get('file')
        # logger.info(f"Received FILES: {request.FILES}")
        if not file_obj or not isinstance(file_obj, UploadedFile):
            logger.error("No valid file uploaded in request")
            return Response({"error": "No valid file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            raw_data = file_obj.read()
            decoded_data = raw_data.decode('utf-8').strip()
            if decoded_data.startswith('\ufeff'):
                decoded_data = decoded_data[1:]

            exercises_data = json.loads(decoded_data)
            logger.info(f"Parsed {len(exercises_data)} exercises from file")
            if not isinstance(exercises_data, list):
                logger.debug("Data is not a list, converting to single-item list")
                exercises_data = [exercises_data]

            # 使用 BulkExerciseSerializer
            bulk_serializer = BulkExerciseSerializer(data=exercises_data)
            if bulk_serializer.is_valid():
                with transaction.atomic():
                    exercises = bulk_serializer.save()
                    count = len(exercises)
                    logger.info(f"Imported {count} exercises by user {request.user.username}")
                    log_user_action(request, 'import', 'Exercise', details={
                        'count': count,
                        'filename': file_obj.name
                    })
                    return Response({
                        "message": f"Successfully imported {count} exercises",
                        "count": count
                    }, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Bulk validation errors: {bulk_serializer.errors}")
                # 格式化错误信息
                error_detail = {
                    "error": "Invalid data",
                    "details": bulk_serializer.errors
                }
                return Response(error_detail, status=status.HTTP_400_BAD_REQUEST)

        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error: {str(e)}")
            return Response({"error": "File must be UTF-8 encoded"}, status=status.HTTP_400_BAD_REQUEST)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return Response({"error": f"Invalid JSON format: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Import error: {str(e)}")
            return Response({"error": f"Server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class UserActionLogListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]  # 保持注释状态
    queryset = UserActionLog.objects.select_related('user').order_by('-timestamp')
    serializer_class = UserActionLogSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        # 定义允许的筛选字段
        filters = {}
        valid_fields = {
            'id': 'id',
            'action_type': 'action_type',
            'model_name': 'model_name',
            'object_id': 'object_id',
            'ip_address': 'ip_address',
            'username': 'user__username',  # 替换 user_id
        }

        # 精确匹配字段
        for param, field in valid_fields.items():
            if param in params:
                value = params.get(param)
                if value:  # 忽略空值
                    filters[field] = value

        # 时间范围筛选
        if 'timestamp_gte' in params:
            try:
                timestamp_gte = parse_datetime(params.get('timestamp_gte'))
                if timestamp_gte:
                    filters['timestamp__gte'] = timestamp_gte
                else:
                    raise ValidationError({"timestamp_gte": "Invalid datetime format"})
            except ValueError:
                raise ValidationError({"timestamp_gte": "Invalid datetime format"})

        if 'timestamp_lte' in params:
            try:
                timestamp_lte = parse_datetime(params.get('timestamp_lte'))
                if timestamp_lte:
                    filters['timestamp__lte'] = timestamp_lte
                else:
                    raise ValidationError({"timestamp_lte": "Invalid datetime format"})
            except ValueError:
                raise ValidationError({"timestamp_lte": "Invalid datetime format"})

        # 应用筛选
        if filters:
            queryset = queryset.filter(**filters)

        return queryset

class UserActionLogDeleteView(generics.DestroyAPIView):
    queryset = UserActionLog.objects.all()
    permission_classes = [IsAdminUser]
    lookup_field = 'id'