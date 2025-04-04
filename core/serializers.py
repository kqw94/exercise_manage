# core/serializers.py
from rest_framework import serializers
from .models import (
    Category, Major, Chapter, ExamGroup, Exercise, ExerciseStem, Question,
    ExerciseAnswer, ExerciseAnalysis
)
import logging

logger = logging.getLogger(__name__)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['category_id', 'category_name']

class MajorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Major
        fields = ['major_id', 'major_name']

class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ['chapter_id', 'chapter_name']

class ExamGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamGroup
        fields = ['examgroup_id', 'examgroup_name']

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['question_id', 'question_order', 'question_stem', 'question_answer', 'question_analysis']
        read_only_fields = [] 

class ExerciseAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseAnswer
        fields = ['answer_id', 'answer_content', 'mark', 'from_model', 'render_type']

class ExerciseAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseAnalysis
        fields = ['analysis_id', 'analysis_content', 'mark', 'render_type']


class ExerciseSerializer(serializers.ModelSerializer):
    stem = serializers.CharField(source='stem.stem_content')  # 移除 read_only，支持写入
    questions = QuestionSerializer(many=True)  # 支持写入
    answer = ExerciseAnswerSerializer()  # 支持写入
    analysis = ExerciseAnalysisSerializer()  # 支持写入
    answers = serializers.SerializerMethodField()
    analyses = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = ['exercise_id', 'stem', 'questions', 'answer', 'analysis', 'answers', 'analyses']

    def get_answers(self, obj):
        answers = ExerciseAnswer.objects.filter(exercise=obj)
        return ExerciseAnswerSerializer(answers, many=True).data

    def get_analyses(self, obj):
        analyses = ExerciseAnalysis.objects.filter(exercise=obj)
        return ExerciseAnalysisSerializer(analyses, many=True).data

   