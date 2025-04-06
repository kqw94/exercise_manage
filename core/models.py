from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.contenttypes.models import ContentType

class Exercise(models.Model):
    exercise_id = models.CharField(max_length=50, primary_key=True)
    exercise_type = models.ForeignKey('ExerciseType', on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, db_index=True)
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
    exercise = models.ForeignKey(Exercise, related_name='answers', on_delete=models.CASCADE)
    answer_content = models.TextField(blank=True, null=True) 
    mark = models.CharField(max_length=100, null=True)
    from_model = models.CharField(max_length=20, blank=True, null=True)
    render_type = models.CharField(max_length=20, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    text1 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercise_answers'


class ExerciseAnalysis(models.Model):
    analysis_id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercise, related_name='analyses', on_delete=models.CASCADE)
    analysis_content = models.TextField()
    mark = models.CharField(max_length=20, null=True)
    from_model = models.CharField(max_length=20, blank=True, null=True)  # 新增字段
    render_type = models.CharField(max_length=20, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    text1 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercise_analysis'




class ExerciseFrom(models.Model):
    exercise = models.OneToOneField(Exercise, on_delete=models.CASCADE, primary_key=True)
    exam = models.ForeignKey('Exam', on_delete=models.SET_NULL, null=True)
    is_official_exercise = models.IntegerField(blank=True, null=True)
    exercise_number = models.IntegerField(default=1, blank=True, null=True)
    material_name = models.CharField(max_length=100,blank=True, null=True)
    section = models.CharField(max_length=100,blank=True, null=True)
    page_number = models.IntegerField(blank=True, null=True)
    text1 = models.TextField(blank=True, null=True)
   
    class Meta:
        db_table = 'exercise_from'



class ExerciseImage(models.Model):
    # 定义第一个字段的选择项
    SOURCE_TYPES = (
        ('stem', 'Stem'),        # 题干
        ('question', 'Question'), # 问题
        ('answer', 'Answer'),     # 答案
        ('analysis', 'Analysis'), # 解析
    )
    image_id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='exercise_images')
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

class School(models.Model):
    school_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)  # 学校名称，唯一约束

    class Meta:
        db_table = 'schools'

class Exam(models.Model):
    exam_id = models.AutoField(primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,  related_name='exams', null=True)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, related_name='exams', null=True, blank=True)  # 新增外键
    from_school = models.CharField(max_length=100,blank=True, null=True)
    exam_time = models.CharField(max_length=20, blank=True, null=True)
    exam_code = models.CharField(max_length=20, blank=True, null=True)
    exam_full_name = models.CharField(max_length=100, blank=True, null=True)
    text1 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exams'

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


class KnowledgeTag(models.Model):
    tag_id = models.CharField(max_length=50, primary_key=True)
    tag_name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,  related_name='knowledge_tags', null=True)
    text1 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'knowledge_tags'


class ExerciseKnowledgeTag(models.Model):
    id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    tag = models.ForeignKey(KnowledgeTag, on_delete=models.CASCADE)

    class Meta:
        db_table = 'exercise_knowledge_tags'


# 角色表
class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)  # 角色名称，例如 'user', 'editor', 'admin'
    description = models.TextField(blank=True, null=True)  # 角色描述，可选

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # 同步创建或更新对应的 Group
        group, created = Group.objects.get_or_create(name=self.name)
        super().save(*args, **kwargs)
        # 将 Role 与 Group 关联（如果需要额外的关联表，可以再设计）
        if not self.groups.filter(id=group.id).exists():
            self.groups.add(group)

    # 与 Group 的多对多关系（可选，用于更灵活的管理）
    groups = models.ManyToManyField(Group, related_name='roles', blank=True)


# 用户表
class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    phone = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # 同步更新用户的 Group
        if self.role:
            group, _ = Group.objects.get_or_create(name=self.role.name)
            self.groups.clear()
            self.groups.add(group)


# 角色权限表
class RolePermission(models.Model):
    id = models.AutoField(primary_key=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    model_name = models.CharField(max_length=50)  # 模型名，例如 'Exercise', 'Category'
    can_create = models.BooleanField(default=False)
    can_read = models.BooleanField(default=True)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'role_permissions'
        unique_together = ('role', 'model_name')  # 每个角色对每个模型的权限唯一

    def __str__(self):
        return f"{self.role.name} - {self.model_name}"
    

class UserActionLog(models.Model):
    ACTION_TYPES = (
        ('create', '创建'),
        ('read', '读取'),
        ('update', '更新'),
        ('delete', '删除'),
        ('login', '登录'),
        ('logout', '登出'),
    )
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=50, blank=True, null=True)  # 操作的模型，例如 'Exercise'
    object_id = models.CharField(max_length=50, blank=True, null=True)  # 操作的对象 ID
    details = models.TextField(blank=True, null=True)  # 操作详情（JSON 或文本）
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)  # 用户 IP 地址

    class Meta:
        db_table = 'user_action_logs'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} - {self.action_type} - {self.timestamp}"





