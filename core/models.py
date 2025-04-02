from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. Exercises（题目表）
class Exercise(models.Model):
    exercise_id = models.CharField(max_length=50, primary_key=True)
    exercise_type = models.ForeignKey('ExerciseType', on_delete=models.SET_NULL, null=True)
    major = models.ForeignKey('Major', on_delete=models.SET_NULL, null=True)
    chapter = models.ForeignKey('Chapter', on_delete=models.SET_NULL, null=True)
    exam_group = models.ForeignKey('ExamGroup', on_delete=models.SET_NULL, null=True)
    source = models.ForeignKey('Source', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercises'

# 2. Questions（选项表）
class Question(models.Model):
    question_id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    question_order = models.IntegerField(default=0)
    question_stem = models.TextField(blank=True, null=True)
    question_answer = models.TextField()
    question_analysis = models.TextField(blank=True, null=True)
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'questions'

# 3. ExerciseAnswers（答案表）
class ExerciseAnswer(models.Model):
    answer_id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    answer = models.TextField(blank=True, null=True) 
    answer_ds = models.TextField(blank=True, null=True)
    answer_gpt = models.TextField(blank=True, null=True)
    answer_proofread = models.TextField(blank=True, null=True)
    answer_quality_check = models.TextField(blank=True, null=True)
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercise_answers'

# 4. ExerciseAnalyses（解析表）
class ExerciseAnalysis(models.Model):
    analysis_id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    analysis = models.TextField()
    analysis_ds = models.TextField(blank=True, null=True)
    analysis_gpt = models.TextField(blank=True, null=True)
    analysis_proofread = models.TextField(blank=True, null=True)
    analysis_quality_check = models.TextField(blank=True, null=True)
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercise_analyses'

# 5. ExerciseFrom（题目来源表）
class ExerciseFrom(models.Model):
    exercise = models.OneToOneField(Exercise, on_delete=models.CASCADE, primary_key=True)
    exam = models.ForeignKey('Exam', on_delete=models.SET_NULL, null=True)
    is_official_exercise = models.IntegerField(blank=True, null=True)
    exercise_number = models.IntegerField(blank=True, null=True)
    material_name = models.CharField(max_length=100,blank=True, null=True)
    section = models.CharField(max_length=100,blank=True, null=True)
    page_number = models.IntegerField(blank=True, null=True)
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercise_from'

# 6. Exams（考试表）
class Exam(models.Model):
    exam_id = models.AutoField(primary_key=True)
    from_school = models.CharField(max_length=100,blank=True, null=True)
    exam_time = models.CharField(max_length=20, blank=True, null=True)
    exam_code = models.CharField(max_length=20, blank=True, null=True)
    exam_full_name = models.CharField(max_length=100, blank=True, null=True)
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exams'

# 7. ExerciseProperty（题目属性表）
class ExerciseProperty(models.Model):
    exercise = models.OneToOneField(Exercise, on_delete=models.CASCADE, primary_key=True)
    level = models.IntegerField(default=1)
    score = models.IntegerField(blank=True, null=True)
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercise_property'


# 9. KnowledgeTags（知识标签表）
class KnowledgeTag(models.Model):
    tag_id = models.CharField(max_length=50, primary_key=True)
    tag_name = models.CharField(max_length=100)
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'knowledge_tags'

# 10. ExerciseKnowledgeTags（题目-知识标签关联表）
class ExerciseKnowledgeTag(models.Model):
    id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    tag = models.ForeignKey(KnowledgeTag, on_delete=models.CASCADE)
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercise_knowledge_tags'

# 11. ExerciseImages（图片链接表）
class ExerciseImage(models.Model):
    image_id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    image_type = models.CharField(max_length=20)
    image_link = models.TextField()
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercise_images'

# 12. ExerciseOcrResults（OCR结果表）
class ExerciseOcrResult(models.Model):
    ocr_id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    ocr_type = models.CharField(max_length=20)
    ocr_result = models.TextField()
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercise_ocr_results'

# 13. Categories（分类表）
class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=100)
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'categories'

# 14. Majors（专业表）
class Major(models.Model):
    major_id = models.AutoField(primary_key=True)
    major_name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'majors'

# 15. Chapters（章节表）
class Chapter(models.Model):
    chapter_id = models.AutoField(primary_key=True)
    chapter_name = models.CharField(max_length=100)
    major = models.ForeignKey(Major, on_delete=models.SET_NULL, null=True)
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'chapters'

# 16. ExamGroups（考试组表）
class ExamGroup(models.Model):
    examgroup_id = models.AutoField(primary_key=True)
    examgroup_name = models.CharField(max_length=100,blank=True, null=True)
    chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True)
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exam_groups'

# 17. Sources（来源表）
class Source(models.Model):
    source_id = models.AutoField(primary_key=True)
    source_name = models.CharField(max_length=100)
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'sources'

# 18. ExerciseTypes（题目类型表）
class ExerciseType(models.Model):
    type_id = models.AutoField(primary_key=True)
    type_name = models.CharField(max_length=20)
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercise_types'

# 19. ExerciseStems（题干表）
class ExerciseStem(models.Model):
    stem_id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    stem_content = models.TextField()
    language = models.CharField(max_length=20, default='zh-CN')
    version = models.IntegerField(default=1)  # 默认值是 1，但仍可能未正确应用
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercise_stems'

class User(AbstractUser):
    role = models.CharField(max_length=50, choices=[('admin', '管理员'), ('user', '普通用户')], default='user')

    class Meta:
        db_table = 'users'




# 21. ExerciseEditHistory（编辑历史表）
class ExerciseEditHistory(models.Model):
    edit_id = models.AutoField(primary_key=True)
    target_table = models.CharField(max_length=50)
    target_id = models.CharField(max_length=50)
    editor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    edited_at = models.DateTimeField(auto_now_add=True)
    edit_type = models.CharField(max_length=50)
    edit_description = models.TextField()
    text1 = models.TextField(blank=True, null=True)
    text2 = models.TextField(blank=True, null=True)
    text3 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercise_edit_history'

