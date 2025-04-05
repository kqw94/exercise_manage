# core/serializers.py
from rest_framework import serializers
from .models import (
    Category, Major, Chapter, ExamGroup, Exercise, ExerciseStem, Question,
    ExerciseAnswer, ExerciseAnalysis, ExerciseType, Source, ExerciseFrom, Exam, School
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