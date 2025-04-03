from django.db import models
from django.contrib.auth.models import AbstractUser

class Exercise(models.Model):
    exercise_id = models.CharField(max_length=50, primary_key=True)
    exercise_type = models.ForeignKey('ExerciseType', on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)
    major = models.ForeignKey('Major', on_delete=models.SET_NULL, null=True)
    chapter = models.ForeignKey('Chapter', on_delete=models.SET_NULL, null=True)
    exam_group = models.ForeignKey('ExamGroup', on_delete=models.SET_NULL, null=True)
   
    exercise_from = models.ForeignKey('ExerciseFrom', on_delete=models.SET_NULL, null=True, related_name='exercise_from')

    source = models.ForeignKey('Source', on_delete=models.SET_NULL, null=True)
    stem = models.ForeignKey('ExerciseStem', on_delete=models.SET_NULL, null=True, related_name='exercise_stem')
    answer = models.ForeignKey('ExerciseAnswer',on_delete=models.SET_NULL, null=True, related_name='exercise_answer')
    analysis = models.ForeignKey('ExerciseAnalysis',on_delete=models.SET_NULL, null=True, related_name='exercise_analysis')
    level = models.IntegerField(default=1)
    score = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    text1 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercises'


class ExerciseStem(models.Model):
    stem_id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    stem_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    text1 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercise_stems'


class Question(models.Model):
    question_id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='questions')
    question_order = models.IntegerField(default=0)
    question_stem = models.TextField(blank=True, null=True)
    question_answer = models.TextField()
    question_analysis = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    text1 = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'questions'


class ExerciseAnswer(models.Model):
    answer_id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    answer_content = models.TextField(blank=True, null=True) 
    mark = models.CharField(max_length=100, null=True)
    from_model = models.CharField(max_length=20, null=True)
    render_type = models.CharField(max_length=20, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    text1 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercise_answers'


class ExerciseAnalysis(models.Model):
    analysis_id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    analysis_content = models.TextField()
    mark = models.CharField(max_length=20, null=True)
    render_type = models.CharField(max_length=20, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    text1 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercise_analysis'



class Exam(models.Model):
    exam_id = models.AutoField(primary_key=True)
    from_school = models.CharField(max_length=100,blank=True, null=True)
    exam_time = models.CharField(max_length=20, blank=True, null=True)
    exam_code = models.CharField(max_length=20, blank=True, null=True)
    exam_full_name = models.CharField(max_length=100, blank=True, null=True)
    text1 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exams'


class ExerciseFrom(models.Model):
    exercise = models.OneToOneField(Exercise, on_delete=models.CASCADE, primary_key=True)
    exam = models.ForeignKey('Exam', on_delete=models.SET_NULL, null=True)
    is_official_exercise = models.IntegerField(blank=True, null=True)
    exercise_number = models.IntegerField(blank=True, null=True)
    material_name = models.CharField(max_length=100,blank=True, null=True)
    section = models.CharField(max_length=100,blank=True, null=True)
    page_number = models.IntegerField(blank=True, null=True)
    text1 = models.TextField(blank=True, null=True)
   
    class Meta:
        db_table = 'exercise_from'




class KnowledgeTag(models.Model):
    tag_id = models.CharField(max_length=50, primary_key=True)
    tag_name = models.CharField(max_length=100)
    text1 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'knowledge_tags'


class ExerciseKnowledgeTag(models.Model):
    id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    tag = models.ForeignKey(KnowledgeTag, on_delete=models.CASCADE)

    class Meta:
        db_table = 'exercise_knowledge_tags'


class ExerciseImage(models.Model):
    # 定义第一个字段的选择项
    SOURCE_TYPES = (
        ('stem', 'Stem'),        # 题干
        ('question', 'Question'), # 问题
        ('answer', 'Answer'),     # 答案
        ('analysis', 'Analysis'), # 解析
    )
    image_id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    image_link = models.TextField()
    
    # 新增的第一个字段：表示内容类型
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPES,
        default='stem',  # 可选：设置默认值
    )    
    # 新增的第二个字段：表示是否废弃
    is_deprecated = models.BooleanField(default=False)  # 默认值为 False，表示未废弃
    ocr_result = models.TextField(blank=True, null=True)
    class Meta:
        db_table = 'exercise_images'




class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'categories'


class Major(models.Model):
    major_id = models.AutoField(primary_key=True)
    major_name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'majors'


class Chapter(models.Model):
    chapter_id = models.AutoField(primary_key=True)
    chapter_name = models.CharField(max_length=100)
    major = models.ForeignKey(Major, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'chapters'

# 16. ExamGroups（考试组表）
class ExamGroup(models.Model):
    examgroup_id = models.AutoField(primary_key=True)
    examgroup_name = models.CharField(max_length=100,blank=True, null=True)
    chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'exam_groups'


class Source(models.Model):
    source_id = models.AutoField(primary_key=True)
    source_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'sources'


class ExerciseType(models.Model):
    type_id = models.AutoField(primary_key=True)
    type_name = models.CharField(max_length=20)

    class Meta:
        db_table = 'exercise_types'



class User(AbstractUser):
    role = models.CharField(max_length=50, choices=[('admin', '管理员'), ('user', '普通用户')], default='user')

    class Meta:
        db_table = 'users'





