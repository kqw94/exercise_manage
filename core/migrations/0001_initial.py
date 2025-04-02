# Generated by Django 5.1.7 on 2025-03-30 03:10

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("category_id", models.AutoField(primary_key=True, serialize=False)),
                ("category_name", models.CharField(max_length=100)),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
            ],
            options={
                "db_table": "categories",
            },
        ),
        migrations.CreateModel(
            name="Chapter",
            fields=[
                ("chapter_id", models.AutoField(primary_key=True, serialize=False)),
                ("chapter_name", models.CharField(max_length=100)),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
            ],
            options={
                "db_table": "chapters",
            },
        ),
        migrations.CreateModel(
            name="Exam",
            fields=[
                ("exam_id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "from_school",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("exam_time", models.CharField(blank=True, max_length=20, null=True)),
                ("exam_code", models.CharField(blank=True, max_length=20, null=True)),
                (
                    "exam_full_name",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
            ],
            options={
                "db_table": "exams",
            },
        ),
        migrations.CreateModel(
            name="Exercise",
            fields=[
                (
                    "exercise_id",
                    models.CharField(max_length=50, primary_key=True, serialize=False),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
                (
                    "chapter",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="core.chapter",
                    ),
                ),
            ],
            options={
                "db_table": "exercises",
            },
        ),
        migrations.CreateModel(
            name="ExerciseType",
            fields=[
                ("type_id", models.AutoField(primary_key=True, serialize=False)),
                ("type_name", models.CharField(max_length=20)),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
            ],
            options={
                "db_table": "exercise_types",
            },
        ),
        migrations.CreateModel(
            name="KnowledgeTag",
            fields=[
                (
                    "tag_id",
                    models.CharField(max_length=50, primary_key=True, serialize=False),
                ),
                ("tag_name", models.CharField(max_length=100)),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
            ],
            options={
                "db_table": "knowledge_tags",
            },
        ),
        migrations.CreateModel(
            name="Source",
            fields=[
                ("source_id", models.AutoField(primary_key=True, serialize=False)),
                ("source_name", models.CharField(max_length=100)),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
            ],
            options={
                "db_table": "sources",
            },
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={
                            "unique": "A user with that username already exists."
                        },
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[
                            django.contrib.auth.validators.UnicodeUsernameValidator()
                        ],
                        verbose_name="username",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True, max_length=254, verbose_name="email address"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[("admin", "管理员"), ("user", "普通用户")],
                        default="user",
                        max_length=50,
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "db_table": "users",
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="ExamGroup",
            fields=[
                ("examgroup_id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "examgroup_name",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
                (
                    "chapter",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="core.chapter",
                    ),
                ),
            ],
            options={
                "db_table": "exam_groups",
            },
        ),
        migrations.CreateModel(
            name="ExerciseProperty",
            fields=[
                (
                    "exercise",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to="core.exercise",
                    ),
                ),
                ("level", models.IntegerField(default=1)),
                ("score", models.IntegerField(blank=True, null=True)),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
            ],
            options={
                "db_table": "exercise_property",
            },
        ),
        migrations.AddField(
            model_name="exercise",
            name="exam_group",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="core.examgroup",
            ),
        ),
        migrations.CreateModel(
            name="ExerciseAnalysis",
            fields=[
                ("analysis_id", models.AutoField(primary_key=True, serialize=False)),
                ("analysis", models.TextField()),
                ("analysis_ds", models.TextField(blank=True, null=True)),
                ("analysis_gpt", models.TextField(blank=True, null=True)),
                ("analysis_proofread", models.TextField(blank=True, null=True)),
                ("analysis_quality_check", models.TextField(blank=True, null=True)),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
                (
                    "exercise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.exercise"
                    ),
                ),
            ],
            options={
                "db_table": "exercise_analyses",
            },
        ),
        migrations.CreateModel(
            name="ExerciseAnswer",
            fields=[
                ("answer_id", models.AutoField(primary_key=True, serialize=False)),
                ("answer", models.TextField(blank=True, null=True)),
                ("answer_ds", models.TextField(blank=True, null=True)),
                ("answer_gpt", models.TextField(blank=True, null=True)),
                ("answer_proofread", models.TextField(blank=True, null=True)),
                ("answer_quality_check", models.TextField(blank=True, null=True)),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
                (
                    "exercise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.exercise"
                    ),
                ),
            ],
            options={
                "db_table": "exercise_answers",
            },
        ),
        migrations.CreateModel(
            name="ExerciseEditHistory",
            fields=[
                ("edit_id", models.AutoField(primary_key=True, serialize=False)),
                ("target_table", models.CharField(max_length=50)),
                ("target_id", models.CharField(max_length=50)),
                ("edited_at", models.DateTimeField(auto_now_add=True)),
                ("edit_type", models.CharField(max_length=50)),
                ("edit_description", models.TextField()),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
                (
                    "editor",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "exercise_edit_history",
            },
        ),
        migrations.CreateModel(
            name="ExerciseImage",
            fields=[
                ("image_id", models.AutoField(primary_key=True, serialize=False)),
                ("image_type", models.CharField(max_length=20)),
                ("image_link", models.TextField()),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
                (
                    "exercise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.exercise"
                    ),
                ),
            ],
            options={
                "db_table": "exercise_images",
            },
        ),
        migrations.CreateModel(
            name="ExerciseOcrResult",
            fields=[
                ("ocr_id", models.AutoField(primary_key=True, serialize=False)),
                ("ocr_type", models.CharField(max_length=20)),
                ("ocr_result", models.TextField()),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
                (
                    "exercise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.exercise"
                    ),
                ),
            ],
            options={
                "db_table": "exercise_ocr_results",
            },
        ),
        migrations.CreateModel(
            name="ExerciseStem",
            fields=[
                ("stem_id", models.AutoField(primary_key=True, serialize=False)),
                ("stem_content", models.TextField()),
                ("language", models.CharField(default="zh-CN", max_length=20)),
                ("version", models.IntegerField(default=1)),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
                (
                    "exercise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.exercise"
                    ),
                ),
            ],
            options={
                "db_table": "exercise_stems",
            },
        ),
        migrations.AddField(
            model_name="exercise",
            name="exercise_type",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="core.exercisetype",
            ),
        ),
        migrations.CreateModel(
            name="ExerciseKnowledgeTag",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
                (
                    "exercise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.exercise"
                    ),
                ),
                (
                    "tag",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.knowledgetag",
                    ),
                ),
            ],
            options={
                "db_table": "exercise_knowledge_tags",
            },
        ),
        migrations.CreateModel(
            name="Major",
            fields=[
                ("major_id", models.AutoField(primary_key=True, serialize=False)),
                ("major_name", models.CharField(max_length=100)),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
                (
                    "category",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="core.category",
                    ),
                ),
            ],
            options={
                "db_table": "majors",
            },
        ),
        migrations.AddField(
            model_name="exercise",
            name="major",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.SET_NULL, to="core.major"
            ),
        ),
        migrations.AddField(
            model_name="chapter",
            name="major",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.SET_NULL, to="core.major"
            ),
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("question_id", models.AutoField(primary_key=True, serialize=False)),
                ("question_order", models.IntegerField(default=0)),
                ("question_stem", models.TextField(blank=True, null=True)),
                ("question_answer", models.TextField()),
                ("question_analysis", models.TextField(blank=True, null=True)),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
                (
                    "exercise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.exercise"
                    ),
                ),
            ],
            options={
                "db_table": "questions",
            },
        ),
        migrations.AddField(
            model_name="exercise",
            name="source",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="core.source",
            ),
        ),
        migrations.CreateModel(
            name="ExerciseFrom",
            fields=[
                (
                    "exercise",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to="core.exercise",
                    ),
                ),
                ("is_official_exercise", models.IntegerField(blank=True, null=True)),
                ("exercise_number", models.IntegerField(blank=True, null=True)),
                (
                    "material_name",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("section", models.CharField(blank=True, max_length=100, null=True)),
                ("page_number", models.IntegerField(blank=True, null=True)),
                ("text1", models.TextField(blank=True, null=True)),
                ("text2", models.TextField(blank=True, null=True)),
                ("text3", models.TextField(blank=True, null=True)),
                (
                    "exam",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="core.exam",
                    ),
                ),
            ],
            options={
                "db_table": "exercise_from",
            },
        ),
    ]
