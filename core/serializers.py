# core/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from django.db import transaction

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

class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['school_id', 'name']


class ExamSerializer(serializers.ModelSerializer):

    category = serializers.SlugRelatedField(queryset=Category.objects.all(), slug_field='category_name', required=False)
    school_write = SchoolSerializer(write_only=True, required=False)  # 用于写入嵌套的 school 数据

    class Meta:
        model = Exam
        fields = ['exam_id', 'exam_code', 'exam_time', 'school', 'school_write', 'from_school', 'exam_full_name', 'category']

    def create(self, validated_data):
        school_data = validated_data.pop('school_write', None)
        if school_data:
            school, _ = School.objects.get_or_create(name=school_data['name'])  # 根据 name 获取或创建
            validated_data['school'] = school
            # 如果 from_school 未提供，自动填充 school.name
            if not validated_data.get('from_school'):
                validated_data['from_school'] = school.name
        return Exam.objects.create(**validated_data)
    

class ExerciseStemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseStem
        fields = ['stem_content']

class ExerciseFromSerializer(serializers.ModelSerializer):
    exam = serializers.PrimaryKeyRelatedField(queryset=Exam.objects.all(), required=False, allow_null=True)
    exam_write = ExamSerializer(write_only=True, required=False)

    class Meta:
        model = ExerciseFrom
        fields = ['exam', 'exam_write', 'is_official_exercise', 'exercise_number', 'material_name', 'section', 'page_number']

    def create(self, validated_data):
        logger.debug(f'watch exercise_from validated_data {validated_data}')
        exam_data = validated_data.pop('exam_write', None)
        if exam_data:
            exam_serializer = ExamSerializer(data=exam_data)
            exam_serializer.is_valid(raise_exception=True)
            exam = exam_serializer.save()
            validated_data['exam'] = exam
        return ExerciseFrom.objects.create(**validated_data)
    

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
    stem = serializers.CharField(source='stem.stem_content', read_only=True)  # 只读
    questions = QuestionSerializer(many=True, read_only=True)
    answer = ExerciseAnswerSerializer(read_only=True)
    analysis = ExerciseAnalysisSerializer(read_only=True)
    exercise_from = ExerciseFromSerializer(read_only=True)
    answers = serializers.SerializerMethodField()
    analyses = serializers.SerializerMethodField()
    from_school = serializers.CharField(source='exercise_from.exam.from_school', read_only=True, allow_null=True)
    exam_time = serializers.CharField(source='exercise_from.exam.exam_time', read_only=True, allow_null=True)
    exam_code = serializers.CharField(source='exercise_from.exam.exam_code', read_only=True, allow_null=True)
    exam_full_name = serializers.CharField(source='exercise_from.exam.exam_full_name', read_only=True, allow_null=True)
    category_name = serializers.CharField(source='category.category_name', read_only=True, allow_null=True)
    major_name = serializers.CharField(source='major.major_name', read_only=True, allow_null=True)
    chapter_name = serializers.CharField(source='chapter.chapter_name', read_only=True, allow_null=True)
    examgroup_name = serializers.CharField(source='exam_group.examgroup_name', read_only=True, allow_null=True)
    source_name = serializers.CharField(source='source.source_name', read_only=True, allow_null=True)

    # 写入字段
    stem_write = ExerciseStemSerializer(source='stem', write_only=True, required=False, allow_null=True)
    questions_write = QuestionSerializer(many=True, source='questions', write_only=True, required=False)
    answer_write = ExerciseAnswerSerializer(many=True, source='answers', write_only=True, required=False)
    analysis_write = ExerciseAnalysisSerializer(many=True, source='analyses', write_only=True, required=False)
    exercise_from_write = ExerciseFromSerializer(source='exercise_from', write_only=True, required=False)
    exam_write = ExamSerializer( write_only=True, required=False)
    school_write = SchoolSerializer( write_only=True, required=False)
    

    # 自定义外键字段支持名称
    category = serializers.CharField()
    major = serializers.CharField()
    chapter = serializers.CharField()
    exam_group = serializers.CharField()
    source = serializers.CharField()
    exercise_type = serializers.CharField()

    class Meta:
        model = Exercise
        fields = [
            'exercise_id', 'exercise_type', 'category', 'major', 'chapter', 'exam_group',
            'source', 'level', 'score', 'stem', 'questions', 'answer', 'analysis',
            'exercise_from', 'answers', 'analyses', 'from_school', 'exam_time', 'exam_code',
            'exam_full_name', 'category_name', 'major_name', 'chapter_name', 'examgroup_name',
            'source_name', 'stem_write', 'questions_write', 'answer_write', 'analysis_write',
            'exercise_from_write', 'exam_write', 'school_write'
        ]
        read_only_fields = ['exercise_id', 'stem', 'questions', 'answer', 'analysis', 'exercise_from']


    def get_answers(self, obj):
        answers = ExerciseAnswer.objects.filter(exercise=obj)
        return ExerciseAnswerSerializer(answers, many=True).data

    def get_analyses(self, obj):
        analyses = ExerciseAnalysis.objects.filter(exercise=obj)
        return ExerciseAnalysisSerializer(analyses, many=True).data

    def validate(self, data):
        logger.debug(f'before validate data {data}')
        errors = {}
        
        # 检查必填字段是否存在
        required_fields = ['category', 'major', 'chapter', 'exam_group', 'source', 'exercise_type']
        for field in required_fields:
            if field not in data or not data[field]:
                errors[field] = f"{field} is required and cannot be empty."
        
       

        if errors:
            raise serializers.ValidationError(errors)
        
        logger.debug(f'validate result is {data}')
        
        return data


    def create(self, validated_data):
        
        stem_data = validated_data.pop('stem_write', None)
        questions_data = validated_data.pop('questions_write', [])
        answers_data = validated_data.pop('answer_write', [])
        analyses_data = validated_data.pop('analysis_write', [])
        exercise_from_data = validated_data.pop('exercise_from_write', None)
        logger.debug('In ExerciseSerializer create.....')

        with transaction.atomic():
            # 映射外键对象
            validated_data['category'] = Category.objects.get(category_name=validated_data.pop('category'))
            validated_data['major'] = Major.objects.get(major_name=validated_data.pop('major'))
            validated_data['chapter'] = Chapter.objects.get(chapter_name=validated_data.pop('chapter'))
            validated_data['exam_group'] = ExamGroup.objects.get(examgroup_name=validated_data.pop('exam_group'))
            validated_data['source'] = Source.objects.get(source_name=validated_data.pop('source'))
            validated_data['exercise_type'] = ExerciseType.objects.get(type_name=validated_data.pop('exercise_type'))

            # 创建 Exercise 对象
            validated_data.pop('exercise_id', None)
            exercise = Exercise.objects.create(**validated_data)

            # 处理 stem
            if stem_data:
                stem = ExerciseStem.objects.create(exercise=exercise, **stem_data)
                exercise.stem = stem

            # 处理 answers，取最后一个
            if answers_data:
                ExerciseAnswer.objects.bulk_create([
                    ExerciseAnswer(exercise=exercise, **data) for data in answers_data
                ])
                exercise.answer = ExerciseAnswer.objects.filter(exercise=exercise).last()

            # 处理 analyses，取最后一个
            if analyses_data:
                ExerciseAnalysis.objects.bulk_create([
                    ExerciseAnalysis(exercise=exercise, **data) for data in analyses_data
                ])
                exercise.analysis = ExerciseAnalysis.objects.filter(exercise=exercise).last()

            # 处理 exercise_from
            if exercise_from_data:
                exam_data = exercise_from_data.pop('exam_write', None)
                if exam_data:
                    school_data = exam_data.pop('school_write', None)
                    if school_data:
                        school, _ = School.objects.get_or_create(name=school_data['name'])
                        exam_data['school'] = school
                        if not exam_data.get('from_school'):
                            exam_data['from_school'] = school.name
                    exam_data['category'] = Category.objects.get(category_name=exam_data.pop('category'))
                    exam, _ = Exam.objects.get_or_create(**exam_data)
                    exercise_from_data['exam'] = exam
                exercise_from = ExerciseFrom.objects.create(exercise=exercise, **exercise_from_data)
                exercise.exercise_from = exercise_from

                

            # 处理 questions
            if questions_data:
                Question.objects.bulk_create([
                    Question(exercise=exercise, **data) for data in questions_data
                ])

            exercise.save(update_fields=['stem', 'answer', 'analysis', 'exercise_from'])
        return exercise



class BulkExerciseSerializer(serializers.ListSerializer):
    child = ExerciseSerializer()

    def create(self, validated_data_list):
        logger.debug(f"Calling BulkExerciseSerializer.create with {len(validated_data_list)} items")
        with transaction.atomic():
            # 预加载外键对象
            categories = {c.category_name: c for c in Category.objects.all()}
            majors = {m.major_name: m for m in Major.objects.all()}
            chapters = {c.chapter_name: c for c in Chapter.objects.all()}
            exam_groups = {e.examgroup_name: e for e in ExamGroup.objects.all()}
            sources = {s.source_name: s for s in Source.objects.all()}
            exercise_types = {t.type_name: t for t in ExerciseType.objects.all()}
            schools = {s.name: s for s in School.objects.all()}

            logger.debug(f"validated_data_list: {validated_data_list}")

            # 第一步：创建并保存 Exercise 对象
            exercises_to_create = []
            for data in validated_data_list:
                logger.debug(f"data: {data}")
                validated_data = {
                    'category': categories.get(data.pop('category')),
                    'major': majors.get(data.pop('major')),
                    'chapter': chapters.get(data.pop('chapter')),
                    'exam_group': exam_groups.get(data.pop('exam_group')),
                    'source': sources.get(data.pop('source')),
                    'exercise_type': exercise_types.get(data.pop('exercise_type')),
                    'level': data.pop('level', None),
                    'score': data.pop('score', None),
                }
                exercises_to_create.append(Exercise(**validated_data))

            # 批量保存 Exercise 对象
            Exercise.objects.bulk_create(exercises_to_create, batch_size=100)
            logger.debug(f"Created {len(exercises_to_create)} exercises")

            # 刷新 Exercise 对象，从数据库重新查询
            exercise_ids = [e.exercise_id for e in exercises_to_create if e.exercise_id is not None]
            refreshed_exercises = list(Exercise.objects.filter(exercise_id__in=exercise_ids).order_by('exercise_id'))
            if len(refreshed_exercises) != len(exercises_to_create):
                logger.warning(f"Exercise count mismatch: created {len(exercises_to_create)}, refreshed {len(refreshed_exercises)}")
                refreshed_exercises = Exercise.objects.order_by('-exercise_id')[:len(exercises_to_create)]

            logger.debug(f"Refreshed exercises: {[e.exercise_id for e in refreshed_exercises]}")

            # 第二步：基于刷新后的 Exercise 创建关联对象
            stems_to_create = []
            questions_to_create = []
            answers_to_create = []
            analyses_to_create = []
            exercise_froms_to_create = []
          
            for exercise, data in zip(refreshed_exercises, validated_data_list):
                stem_data = data.pop('stem', None)
                logger.debug(f"stem_data: {stem_data}")
                questions_data = data.pop('questions', [])
                logger.debug(f"questions_data: {questions_data}")
                answers_data = data.pop('answers', [])
                logger.debug(f"answers_data: {answers_data}")
                analyses_data = data.pop('analyses', [])
                logger.debug(f"analyses_data: {analyses_data}")
                exercise_from_data = data.pop('exercise_from', None)
                logger.debug(f"exercise_from_data: {exercise_from_data}")
                

                if stem_data:
                    stems_to_create.append(ExerciseStem(exercise=exercise, **stem_data))
                if questions_data:
                    questions_to_create.extend([Question(exercise=exercise, **q) for q in questions_data])
                if answers_data:
                    answers_to_create.extend([ExerciseAnswer(exercise=exercise, **a) for a in answers_data])
                if analyses_data:
                    analyses_to_create.extend([ExerciseAnalysis(exercise=exercise, **a) for a in analyses_data])
        
                
                if exercise_from_data:
                    exam_data = data.pop('exam_write', None)
                    if exam_data:
                        school_data = data.pop('school_write', None)
                        if school_data:
                            school, _ = School.objects.get_or_create(name=school_data['name'])
                            exam_data['school'] = school
                            if not exam_data.get('from_school'):
                                exam_data['from_school'] = school.name
                        # exam_data['category'] = categories.get(exam_data.pop('category'))
                        exam_data['category'] = validated_data['category']
                        logger.debug(f'watch exam data {exam_data}')
                        exam, _ = Exam.objects.get_or_create(**exam_data)
                        exercise_from_data['exam'] = exam
                    exercise_froms_to_create.append(ExerciseFrom(exercise=exercise, **exercise_from_data))

            logger.debug(f"stems_to_create={stems_to_create}\n"
                         f"questions_to_create={questions_to_create}\n"
                         f"answers_to_create={answers_to_create}\n"
                         f"analyses_to_create={analyses_to_create}\n"
                         f"exercise_froms_to_create={exercise_froms_to_create}")

            # 批量创建关联对象
            ExerciseStem.objects.bulk_create(stems_to_create, batch_size=100)
            logger.debug(f"Created {len(stems_to_create)} stems")
            Question.objects.bulk_create(questions_to_create, batch_size=100)
            logger.debug(f"Created {len(questions_to_create)} questions")
            ExerciseAnswer.objects.bulk_create(answers_to_create, batch_size=100)
            logger.debug(f"Created {len(answers_to_create)} answers")
            ExerciseAnalysis.objects.bulk_create(analyses_to_create, batch_size=100)
            logger.debug(f"Created {len(analyses_to_create)} analyses")
            ExerciseFrom.objects.bulk_create(exercise_froms_to_create, batch_size=100)
            logger.debug(f"Created {len(exercise_froms_to_create)} exercise_froms")

            # 更新外键关系
            for exercise in refreshed_exercises:
                stem = ExerciseStem.objects.filter(exercise_id=exercise.exercise_id).first()
                answer = ExerciseAnswer.objects.filter(exercise_id=exercise.exercise_id).last()
                analysis = ExerciseAnalysis.objects.filter(exercise_id=exercise.exercise_id).last()
                exercise_from = ExerciseFrom.objects.filter(exercise_id=exercise.exercise_id).first()

                logger.debug(f"Exercise {exercise.exercise_id}: "
                            f"stem={stem.stem_id if stem else None}, "
                            f"answer={answer.answer_id if answer else None}, "
                            f"analysis={analysis.analysis_id if analysis else None}, "
                            f"exercise_from={exercise_from.exercise if exercise_from else None}")

                exercise.stem = stem
                exercise.answer = answer
                exercise.analysis = analysis
                exercise.exercise_from = exercise_from
                exercise.save(update_fields=['stem', 'answer', 'analysis', 'exercise_from'])

                exercise.refresh_from_db()
                logger.debug(f"After save - Exercise {exercise.exercise_id}: "
                            f"stem_id={exercise.stem_id}, "
                            f"answer_id={exercise.answer_id}, "
                            f"analysis_id={exercise.analysis_id}, "
                            f"exercise_from_id={exercise.exercise_from_id}")

            return refreshed_exercises



class BulkExerciseUpdateSerializer(serializers.Serializer):
    exercise_ids = serializers.ListField(
        child=serializers.IntegerField(),  # 改为 IntegerField
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