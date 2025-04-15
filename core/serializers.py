# core/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Max

from .models import (
    Category, Major, Chapter, ExamGroup, Exercise, ExerciseStem, Question,
    ExerciseAnswer, ExerciseAnalysis, ExerciseType, Source, ExerciseFrom, Exam, School,
    User, RolePermission, UserActionLog, Role, Source, ExerciseImage
)
import traceback
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
        fields = [ 'question_order', 'question_stem', 'question_answer']

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

class ExerciseImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseImage
        fields = ['image_link', 'source_type', 'is_deprecated', 'ocr_result']

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
    from_school = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    exam_time = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    exam_code = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    exam_full_name = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = ExerciseFrom
        fields = [
            'exam', 'exam_write', 'from_school', 'exam_time', 'exam_code', 'exam_full_name',
            'is_official_exercise', 'exercise_number', 'material_name', 'section', 'page_number'
        ]

    # def validate(self, data):
    #     logger.debug(f"Validating ExerciseFrom data: {data}")
    #     has_exam_write = data.get('exam_write')
    #     has_exam_fields = any(data.get(field) for field in ['from_school', 'exam_time', 'exam_code', 'exam_full_name', 'is_official_exercise', 'section', 'material_name', 'page_number'])
    #     if not data.get('exam') and not has_exam_write and not has_exam_fields:
    #         raise serializers.ValidationError("Must provide either exam, exam_write, or at least one of other fields.")
    #     return data

    def create(self, validated_data):
        logger.debug(f"Creating ExerciseFrom with validated_data: {validated_data}")
        exam_data = validated_data.pop('exam_write', None)
        exam = validated_data.pop('exam', None)
        from_school = validated_data.pop('from_school', None)
        exam_time = validated_data.pop('exam_time', None)
        exam_code = validated_data.pop('exam_code', None)
        exam_full_name = validated_data.pop('exam_full_name', None)
        exercise = validated_data.pop('exercise', None)  # 获取 exercise

        if not exam:
            if exam_data:
                exam_serializer = ExamSerializer(data=exam_data)
                exam_serializer.is_valid(raise_exception=True)
                exam = exam_serializer.save()
            elif any([from_school, exam_time, exam_code, exam_full_name]):
                exam_data = {
                    'from_school': from_school,
                    'exam_time': exam_time,
                    'exam_code': exam_code,
                    'exam_full_name': exam_full_name
                }
                exam_data = {k: v for k, v in exam_data.items() if v is not None}
                if exam_data:
                    if from_school:
                        school, _ = School.objects.get_or_create(name=from_school)
                        exam_data['school'] = school
                    if exercise and exercise.category:
                        exam_data['category'] = exercise.category
                    exam, _ = Exam.objects.get_or_create(**exam_data)
                else:
                    exam = None

        if exam:
            validated_data['exam'] = exam
        if exercise:
            validated_data['exercise'] = exercise
        else:
            logger.warning("No exercise provided for ExerciseFrom, may cause null exercise_id")
        return ExerciseFrom(**validated_data)
    

# 新增：题型和来源序列化器
class ExerciseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseType
        fields = ['type_id', 'type_name']

class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ['source_id', 'source_name']




class ExerciseSerializer(serializers.ModelSerializer):
    stem = serializers.CharField(source='stem.stem_content', read_only=True)  # 只读
    questions = QuestionSerializer(many=True, read_only=True)
    answer = ExerciseAnswerSerializer(read_only=True)
    analysis = ExerciseAnalysisSerializer(read_only=True)

    
    from_school = serializers.CharField(source='exercise_from.exam.from_school', read_only=True, allow_null=True)
    exam_time = serializers.CharField(source='exercise_from.exam.exam_time', read_only=True, allow_null=True)
    exam_code = serializers.CharField(source='exercise_from.exam.exam_code', read_only=True, allow_null=True)
    exam_full_name = serializers.CharField(source='exercise_from.exam.exam_full_name', read_only=True, allow_null=True)
    category_name = serializers.CharField(source='category.category_name', read_only=True, allow_null=True)
    major_name = serializers.CharField(source='major.major_name', read_only=True, allow_null=True)
    chapter_name = serializers.CharField(source='chapter.chapter_name', read_only=True, allow_null=True)
    examgroup_name = serializers.CharField(source='exam_group.examgroup_name', read_only=True, allow_null=True)
    source_name = serializers.CharField(source='source.source_name', read_only=True, allow_null=True)
    type_name = serializers.CharField(source='exercise_type.type_name', read_only=True, allow_null=True)

    

    class Meta:
        model = Exercise
        fields = [
            'exercise_id', 
             'level', 'score', 'stem', 'questions', 'answer', 'analysis',
            'from_school', 'exam_time', 'exam_code', 
            'exam_full_name', 'category_name', 'major_name', 'chapter_name', 'examgroup_name',
            'source_name', 'type_name'
        ]
        read_only_fields = ['exercise_id']


    

    def validate(self, data):
        logger.debug(f'before validate data {data}')
        errors = {}
        
        # 检查必填字段是否存在
        # required_fields = ['category', 'major', 'chapter', 'exam_group', 'source', 'exercise_type']
        # for field in required_fields:
        #     if field not in data or not data[field]:
        #         errors[field] = f"{field} is required and cannot be empty."
        
       

        if errors:
            raise serializers.ValidationError(errors)
        
        logger.debug(f'validate result is {data}')
        
        return data







class ExerciseWriteSerializer(serializers.ModelSerializer):
    category = serializers.CharField()
    major = serializers.CharField(allow_null=True)
    chapter = serializers.CharField(allow_null=True)
    examgroup = serializers.CharField(allow_null=True)
    source = serializers.CharField(allow_null=True)
    type = serializers.CharField()
    stem = serializers.CharField(allow_null=True)
    questions = QuestionSerializer(many=True, required=False)
    answer = ExerciseAnswerSerializer(many=True, required=False)
    analysis = ExerciseAnalysisSerializer(many=True, required=False)
    exercise_from = ExerciseFromSerializer(required=False, allow_null=True)
    image_links = ExerciseImageSerializer(many=True, required=False)
    exercise_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Exercise
        fields = [
            'exercise_id', 'category', 'major', 'chapter', 'examgroup', 'source', 'type',
            'level', 'score', 'stem', 'questions', 'answer', 'analysis', 'exercise_from', 'image_links'
        ]

    def to_internal_value(self, data):
        # Log raw input data for debugging
        # logger.debug(f"Raw input data: {data}")
        return super().to_internal_value(data)

    def validate(self, data):
        # logger.debug(f'Validated data: {data}')
        errors = {}

        # Required fields
        required_fields = ['category']
        for field in required_fields:
            if field not in data or not data[field]:
                errors[field] = f"{field} is required and cannot be empty."

        # Validate stem or questions presence
        # if not data.get('stem') and not data.get('questions'):
        #     errors['stem'] = "Either stem or questions must be provided."

        # Validate exercise_id if provided
        if 'exercise_id' in data and data['exercise_id'] is not None:
            try:
                Exercise.objects.get(exercise_id=data['exercise_id'])
                logger.debug(f"Found exercise ID {data['exercise_id']} for update")
            except Exercise.DoesNotExist:
                logger.warning(f"Exercise ID {data['exercise_id']} not found, will create new exercise")
                # Optional: Raise error instead
                # errors['exercise_id'] = f"Exercise ID {data['exercise_id']} does not exist"

        if errors:
            raise serializers.ValidationError(errors)
        return data

    def create(self, validated_data):
        data_list = validated_data if isinstance(validated_data, list) else [validated_data]
        logger.debug(f"Calling create with {len(data_list)} items")

        with transaction.atomic():
            # 预加载外键对象
            # categories = {c.category_name: c for c in Category.objects.all()}
            # majors = {m.major_name: m for m in Major.objects.all()}
            # chapters = {c.chapter_name: c for c in Chapter.objects.all()}
            # exam_groups = {e.examgroup_name: e for e in ExamGroup.objects.all()}
            # sources = {s.source_name: s for s in Source.objects.all()}
            # exercise_types = {t.type_name: t for t in ExerciseType.objects.all()}
            # schools = {s.name: s for s in School.objects.all()}

            # 分离更新和创建
            updates = []
            creations = []
            exercise_id_to_data = {}
            for data in data_list:
                exercise_id = data.pop('exercise_id', None)
                exercise_id_to_data[exercise_id] = data
                if exercise_id is not None:
                    try:
                        exercise = Exercise.objects.get(exercise_id=exercise_id)
                        updates.append((exercise, data))
                    except Exercise.DoesNotExist:
                        creations.append((exercise_id, data))
                else:
                    creations.append((None, data))

            # 处理创建
            exercises_to_create = []
            created_exercise_ids = []
            for exercise_id, data in creations:
                try:
                    category_name = data.pop('category')
                    category, _ = Category.objects.get_or_create(category_name=category_name)
                    major_name = data.pop('major', None)
                    major = None
                    if major_name:
                        major, _ = Major.objects.get_or_create(major_name=major_name, category=category)
                    chapter_name = data.pop('chapter', None)
                    chapter = None
                    if chapter_name and major:
                        chapter, _ = Chapter.objects.get_or_create(chapter_name=chapter_name, major=major)
                    examgroup_name = data.pop('examgroup', None)
                    exam_group = None
                    if examgroup_name and chapter:
                        exam_group, _ = ExamGroup.objects.get_or_create(examgroup_name=examgroup_name, chapter=chapter)
                    source_name = data.pop('source', None)
                    source = None
                    if source_name:
                        source, _ = Source.objects.get_or_create(source_name=source_name)
                    type_name = data.pop('type')
                    exercise_type, _ = ExerciseType.objects.get_or_create(type_name=type_name)

                    exercise_data = {
                        'exercise_id': exercise_id,
                        'category': category,
                        'major': major,
                        'chapter': chapter,
                        'exam_group': exam_group,
                        'source': source,
                        'exercise_type': exercise_type,
                        'level': data.pop('level', None),
                        'score': data.pop('score', None),
                    }
                    if exercise_id is None:
                        max_id = Exercise.objects.aggregate(Max('exercise_id'))['exercise_id__max'] or 0
                        exercise_data['exercise_id'] = max_id + 1
                    exercises_to_create.append(Exercise(**exercise_data))
                    created_exercise_ids.append(exercise_data['exercise_id'])
                except Exception as e:
                    logger.error(f"Failed to process creation for exercise_id={exercise_id}: {str(e)}")
                    continue

            # 初始化 created_exercises
            created_exercises = []
            if exercises_to_create:
                try:
                    Exercise.objects.bulk_create(exercises_to_create, batch_size=100)
                    logger.debug(f"Created {len(exercises_to_create)} new exercises")
                    created_exercises = list(Exercise.objects.filter(exercise_id__in=created_exercise_ids))
                except Exception as e:
                    logger.error(f"Bulk create exercises failed: {str(e)}")
                    raise

            # 处理更新
            updated_exercises = []
            for exercise, data in updates:
                try:
                    logger.debug(f"Updating exercise ID {exercise.exercise_id}")
                    category_name = data.pop('category')
                    category, _ = Category.objects.get_or_create(category_name=category_name)
                    major_name = data.pop('major', None)
                    major = None
                    if major_name:
                        major, _ = Major.objects.get_or_create(major_name=major_name, category=category)
                    chapter_name = data.pop('chapter', None)
                    chapter = None
                    if chapter_name and major:
                        chapter, _ = Chapter.objects.get_or_create(chapter_name=chapter_name, major=major)
                    examgroup_name = data.pop('examgroup', None)
                    exam_group = None
                    if examgroup_name and chapter:
                        exam_group, _ = ExamGroup.objects.get_or_create(examgroup_name=examgroup_name, chapter=chapter)
                    source_name = data.pop('source', None)
                    source = None
                    if source_name:
                        source, _ = Source.objects.get_or_create(source_name=source_name)
                    type_name = data.pop('type')
                    exercise_type, _ = ExerciseType.objects.get_or_create(type_name=type_name)

                    exercise.category = category
                    exercise.major = major
                    exercise.chapter = chapter
                    exercise.exam_group = exam_group
                    exercise.source = source
                    exercise.exercise_type = exercise_type
                    exercise.level = data.pop('level', None)
                    exercise.score = data.pop('score', None)
                    exercise.save()

                    ExerciseStem.objects.filter(exercise=exercise).delete()
                    Question.objects.filter(exercise=exercise).delete()
                    ExerciseAnswer.objects.filter(exercise=exercise).delete()
                    ExerciseAnalysis.objects.filter(exercise=exercise).delete()
                    ExerciseFrom.objects.filter(exercise=exercise).delete()
                    ExerciseImage.objects.filter(exercise=exercise).delete()

                    updated_exercises.append(exercise)
                except Exception as e:
                    logger.error(f"Failed to update exercise_id={exercise.exercise_id}: {str(e)}")
                    continue

            all_exercises = created_exercises + updated_exercises
            all_data = [exercise_id_to_data.get(ex.exercise_id, {}) for ex in all_exercises]

            if not all_exercises:
                logger.warning("No exercises created or updated, returning empty list")
                return []

            stems_to_create = []
            questions_to_create = []
            answers_to_create = []
            analyses_to_create = []
            exercise_froms_to_create = []
            images_to_create = []

            for exercise, data in zip(all_exercises, all_data):
                logger.debug(f"Processing related objects for exercise_id={exercise.exercise_id}")
                stem_content = data.pop('stem', None)
                questions_data = data.pop('questions', [])
                answers_data = data.pop('answer', [])
                analyses_data = data.pop('analysis', [])
                exercise_from_data = data.pop('exercise_from', None)
                image_links_data = data.pop('image_links', [])

                if stem_content:
                    stems_to_create.append(ExerciseStem(exercise=exercise, stem_content=stem_content))

                if questions_data:
                    question_serializer = QuestionSerializer(data=questions_data, many=True)
                    if question_serializer.is_valid():
                        validated_questions = question_serializer.validated_data
                        seen_orders = set()
                        for q in validated_questions:
                            q_order = q.get('question_order')
                            if q_order is not None:
                                if q_order in seen_orders:
                                    logger.warning(
                                        f"Duplicate question_order {q_order} for exercise_id={exercise.exercise_id}"
                                    )
                                    continue
                                seen_orders.add(q_order)
                            questions_to_create.append(
                                Question(
                                    exercise=exercise,
                                    question_order=q.get('question_order'),
                                    question_stem=q.get('question_stem', ''),
                                    question_answer=q.get('question_answer', ''),
                                    question_analysis=q.get('question_analysis')
                                )
                            )
                    else:
                        logger.error(f"Question validation errors for exercise_id={exercise.exercise_id}: {question_serializer.errors}")

                if answers_data:
                    answers_to_create.extend([ExerciseAnswer(exercise=exercise, **a) for a in answers_data])
                if analyses_data:
                    analyses_to_create.extend([ExerciseAnalysis(exercise=exercise, **a) for a in analyses_data])

                if exercise_from_data:
                    logger.debug(f"ExerciseFrom data for exercise_id={exercise.exercise_id}: {exercise_from_data}")
                    exercise_from_serializer = ExerciseFromSerializer(data=exercise_from_data)
                    if exercise_from_serializer.is_valid():
                        validated_from_data = exercise_from_serializer.validated_data
                        validated_from_data['exercise'] = exercise
                        exercise_from = exercise_from_serializer.create(validated_from_data)
                        if not exercise_from.exercise:
                            logger.error(f"ExerciseFrom missing exercise for exercise_id={exercise.exercise_id}")
                            exercise_from.exercise = exercise
                        exercise_froms_to_create.append(exercise_from)
                        logger.info(f"Created ExerciseFrom for exercise_id={exercise.exercise_id}, exam_id={exercise_from.exam.exam_id if exercise_from.exam else 'None'}")
                    else:
                        logger.error(f"ExerciseFrom validation errors for exercise_id={exercise.exercise_id}: {exercise_from_serializer.errors}")

                if image_links_data:
                    images_to_create.extend([ExerciseImage(exercise=exercise, **img) for img in image_links_data])

            if stems_to_create:
                ExerciseStem.objects.bulk_create(stems_to_create, batch_size=100)
            if questions_to_create:
                logger.info(f"Creating {len(questions_to_create)} questions")
                Question.objects.bulk_create(questions_to_create, batch_size=100)
            if answers_to_create:
                ExerciseAnswer.objects.bulk_create(answers_to_create, batch_size=100)
            if analyses_to_create:
                ExerciseAnalysis.objects.bulk_create(analyses_to_create, batch_size=100)
            if exercise_froms_to_create:
                logger.info(f"Creating {len(exercise_froms_to_create)} exercise_froms")
                try:
                    ExerciseFrom.objects.bulk_create(exercise_froms_to_create, batch_size=100)
                except Exception as e:
                    logger.error(f"Bulk create ExerciseFrom failed: {str(e)}")
                    raise
            if images_to_create:
                ExerciseImage.objects.bulk_create(images_to_create, batch_size=100)

            for exercise in all_exercises:
                stem = ExerciseStem.objects.filter(exercise=exercise).first()
                answer = ExerciseAnswer.objects.filter(exercise=exercise).last()
                analysis = ExerciseAnalysis.objects.filter(exercise=exercise).last()
                exercise_from = ExerciseFrom.objects.filter(exercise=exercise).first()

                exercise.stem = stem
                exercise.answer = answer
                exercise.analysis = analysis
                exercise.exercise_from = exercise_from
                exercise.save(update_fields=['stem', 'answer', 'analysis', 'exercise_from'])
                exercise.refresh_from_db()

            logger.info(f"Processed {len(all_exercises)} exercises: {len(created_exercises)} created, {len(updated_exercises)} updated")
            return all_exercises

class BulkExerciseSerializer(serializers.ListSerializer):
    child = ExerciseWriteSerializer()

    def create(self, validated_data_list):
        logger.debug(f"Calling BulkExerciseSerializer.create with {len(validated_data_list)} items")
        return self.child.create(validated_data_list)







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
    user_id = serializers.IntegerField(source='user.id', read_only=True, allow_null=True)

    class Meta:
        model = UserActionLog
        fields = ['id', 'user', 'user_id', 'action_type', 'model_name', 'object_id', 'details', 'timestamp', 'ip_address']