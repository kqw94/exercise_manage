from rest_framework import serializers
from .models import Category, Major, Chapter, ExamGroup, Exercise, User, Exam, ExerciseStem,  Question, ExerciseAnswer, ExerciseAnalysis

class ExamGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamGroup
        fields = ['examgroup_id', 'examgroup_name']
        read_only_fields = ['examgroup_id']

class ChapterSerializer(serializers.ModelSerializer):
    exam_groups = ExamGroupSerializer(many=True, read_only=True, source='examgroup_set')
    class Meta:
        model = Chapter
        fields = ['chapter_id', 'chapter_name', 'exam_groups']
        read_only_fields = ['chapter_id']

class MajorSerializer(serializers.ModelSerializer):
    chapters = ChapterSerializer(many=True, read_only=True, source='chapter_set')
    class Meta:
        model = Major
        fields = ['major_id', 'major_name', 'chapters']
        read_only_fields = ['major_id']

class CategorySerializer(serializers.ModelSerializer):
    majors = MajorSerializer(many=True, read_only=True, source='major_set')
    class Meta:
        model = Category
        fields = ['category_id', 'category_name', 'majors']
        read_only_fields = ['category_id']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data.pop('password'))
        return super().update(instance, validated_data)
    

class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ['exam_id', 'exam_full_name', 'from_school', 'exam_time', 'exam_code']

class ExerciseStemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseStem
        fields = ['stem_content']

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['question_stem', 'question_answer']

class ExerciseAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseAnswer
        fields = ['answer']

class ExerciseAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseAnalysis
        fields = ['analysis']

class ExerciseSerializer(serializers.ModelSerializer):
    stem = ExerciseStemSerializer(many=True, source='exercisestem_set')  # 匹配 related_name
    question = QuestionSerializer(many=True, source = 'question_set')  # 默认 related_name='question'
    answer = ExerciseAnswerSerializer(many=True, source='exerciseanswer_set')  # 匹配 related_name
    analysis = ExerciseAnalysisSerializer(many=True, source='exerciseanalysis_set')  # 匹配 related_name

    class Meta:
        model = Exercise
        fields = ['exercise_id', 'stem', 'question', 'answer', 'analysis']

    def update(self, instance, validated_data):
        # 更新 Stem
        stem_data = validated_data.pop('exercisestem_set', [])
        for stem_item, data in zip(instance.exercise_stems.all(), stem_data):
            stem_serializer = ExerciseStemSerializer(stem_item, data=data, partial=True)
            if stem_serializer.is_valid():
                stem_serializer.save()

        # 更新 Question
        question_data = validated_data.pop('question', [])
        for question_item, data in zip(instance.question.all(), question_data):
            question_serializer = QuestionSerializer(question_item, data=data, partial=True)
            if question_serializer.is_valid():
                question_serializer.save()

        # 更新 Answer
        answer_data = validated_data.pop('exercise_answers', [])
        for answer_item, data in zip(instance.exercise_answers.all(), answer_data):
            answer_serializer = ExerciseAnswerSerializer(answer_item, data=data, partial=True)
            if answer_serializer.is_valid():
                answer_serializer.save()

        # 更新 Analysis
        analysis_data = validated_data.pop('exercise_analyses', [])
        for analysis_item, data in zip(instance.exercise_analyses.all(), analysis_data):
            analysis_serializer = ExerciseAnalysisSerializer(analysis_item, data=data, partial=True)
            if analysis_serializer.is_valid():
                analysis_serializer.save()

        return instance