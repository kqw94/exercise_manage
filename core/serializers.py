# core/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group

from .models import (
    Category, Major, Chapter, ExamGroup, Exercise, ExerciseStem, Question,
    ExerciseAnswer, ExerciseAnalysis, ExerciseType, Source, ExerciseFrom, Exam, School,
    User, RolePermission, UserActionLog, Role
)
import logging

logger = logging.getLogger(__name__)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['category_id', 'category_name']


class MajorSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source='category', write_only=True)

    class Meta:
        model = Major
        fields = ['major_id', 'major_name', 'category', 'category_id']

class ChapterSerializer(serializers.ModelSerializer):
    major = MajorSerializer(read_only=True)
    major_id = serializers.PrimaryKeyRelatedField(queryset=Major.objects.all(), source='major', write_only=True)

    class Meta:
        model = Chapter
        fields = ['chapter_id', 'chapter_name', 'major', 'major_id']

class ExamGroupSerializer(serializers.ModelSerializer):
    chapter = ChapterSerializer(read_only=True)
    chapter_id = serializers.PrimaryKeyRelatedField(queryset=Chapter.objects.all(), source='chapter', write_only=True)

    class Meta:
        model = ExamGroup
        fields = ['examgroup_id', 'examgroup_name', 'chapter', 'chapter_id']

class ExerciseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseType
        fields = ['type_id', 'type_name']

class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ['source_id', 'source_name']

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['question_id', 'question_order', 'question_stem', 'question_answer', 'question_analysis']

class ExerciseAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseAnswer
        fields = ['answer_id', 'answer_content', 'mark', 'from_model', 'render_type']

class ExerciseAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseAnalysis
        fields = ['analysis_id', 'analysis_content', 'mark', 'render_type']

class ExamSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False)

    class Meta:
        model = Exam
        fields = ['exam_id', 'exam_code', 'exam_time', 'school','from_school', 'exam_full_name', 'category']

class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['school_id', 'name']

class ExerciseFromSerializer(serializers.ModelSerializer):
    exam = ExamSerializer(read_only=True)  # 添加 exam 的序列化

    class Meta:
        model = ExerciseFrom
        fields = ['exam', 'is_official_exercise', 'exercise_number', 'material_name', 'section', 'page_number']


# 新增：题型和来源序列化器
class ExerciseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseType
        fields = ['type_id', 'type_name']

class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ['source_id', 'source_name']

class ExerciseFromSerializer(serializers.ModelSerializer):
    exam = ExamSerializer(read_only=True)

    class Meta:
        model = ExerciseFrom
        fields = ['exam', 'is_official_exercise', 'exercise_number', 'material_name', 'section', 'page_number']


class ExerciseSerializer(serializers.ModelSerializer):
    stem = serializers.CharField(source='stem.stem_content')
    questions = QuestionSerializer(many=True)
    answer = ExerciseAnswerSerializer()
    analysis = ExerciseAnalysisSerializer()
    exercise_from = ExerciseFromSerializer(read_only=True)
    answers = serializers.SerializerMethodField()
    analyses = serializers.SerializerMethodField()
    # 新增字段
    from_school = serializers.CharField(source='exercise_from.exam.from_school', read_only=True, allow_null=True)
    exam_time = serializers.CharField(source='exercise_from.exam.exam_time', read_only=True, allow_null=True)
    exam_code = serializers.CharField(source='exercise_from.exam.exam_code', read_only=True, allow_null=True)
    exam_full_name = serializers.CharField(source='exercise_from.exam.exam_full_name', read_only=True, allow_null=True)
    category_name = serializers.CharField(source='category.category_name', read_only=True, allow_null=True)
    major_name = serializers.CharField(source='major.major_name', read_only=True, allow_null=True)
    chapter_name = serializers.CharField(source='chapter.chapter_name', read_only=True, allow_null=True)
    examgroup_name = serializers.CharField(source='exam_group.examgroup_name', read_only=True, allow_null=True)
    source_name = serializers.CharField(source='source.source_name', read_only=True, allow_null=True)
    
    class Meta:
        model = Exercise
        fields = [
            'exercise_id', 'exercise_type', 'category_name', 'major_name', 'chapter_name', 'examgroup_name',
            'source_name', 'level', 'score', 'stem', 'questions', 'answer', 'analysis',
            'exercise_from', 'answers', 'analyses',
            'from_school', 'exam_time', 'exam_code', 'exam_full_name'  # 新增字段
        ]

    def get_answers(self, obj):
        answers = ExerciseAnswer.objects.filter(exercise=obj)
        return ExerciseAnswerSerializer(answers, many=True).data

    def get_analyses(self, obj):
        analyses = ExerciseAnalysis.objects.filter(exercise=obj)
        return ExerciseAnalysisSerializer(analyses, many=True).data

class BulkExerciseUpdateSerializer(serializers.Serializer):
    exercise_ids = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of exercise IDs to update"
    )
    exam_group = serializers.IntegerField(required=False, allow_null=True)
    level = serializers.IntegerField(required=False, min_value=1, max_value=5, allow_null=True)
    score = serializers.FloatField(required=False, min_value=0, allow_null=True)

    def validate_exercise_ids(self, value):
        if not value:
            raise serializers.ValidationError("Exercise IDs list cannot be empty")
        # 检查所有 ID 是否存在
        existing_ids = Exercise.objects.filter(exercise_id__in=value).values_list('exercise_id', flat=True)
        missing_ids = set(value) - set(existing_ids)
        if missing_ids:
            raise serializers.ValidationError(f"Exercises not found: {missing_ids}")
        return value
    


# 角色序列化器
class RoleSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(
        many=True, slug_field='name', queryset=Group.objects.all(), required=False
    )

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'groups']


# 用户注册序列化器
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'role', 'phone']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        role = validated_data.pop('role', None) or Role.objects.get(name='user')  # 默认角色为 'user'
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            phone=validated_data.get('phone', ''),
            role=role
        )
        return user


# 用户登录序列化器（不变）
class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid credentials")


# 用户信息序列化器
class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)  # 只读，用于返回数据
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), source='role', required=False, allow_null=True, write_only=True
    )  # 用于接收 ID
    groups = serializers.SlugRelatedField(
        many=True, slug_field='name', queryset=Group.objects.all(), required=False
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'role_id', 'phone', 'is_active', 'groups', 'date_joined']
        read_only_fields = ['date_joined']



# 角色权限序列化器
class RolePermissionSerializer(serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())

    class Meta:
        model = RolePermission
        fields = ['id', 'role', 'model_name', 'can_create', 'can_read', 'can_update', 'can_delete']


# 用户操作日志序列化器（不变）
class UserActionLogSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = UserActionLog
        fields = ['id', 'user', 'action_type', 'model_name', 'object_id', 'details', 'timestamp', 'ip_address']