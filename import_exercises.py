import json
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import (
    Exercise, ExerciseStem, Question, ExerciseAnswer, ExerciseAnalysis,
    ExerciseFrom, ExerciseImage, Category, Major, Chapter, ExamGroup,
    Source, ExerciseType, School, Exam
)


class Command(BaseCommand):
    help = 'Import exercise data from a JSON file into the database'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file containing exercise data')

    def handle(self, *args, **options):
        json_file = options['json_file']

        # 读取 JSON 文件
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                exercises_data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File {json_file} not found"))
            return
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f"Invalid JSON format in {json_file}"))
            return

        # 如果数据是单个对象，转换为列表
        if not isinstance(exercises_data, list):
            exercises_data = [exercises_data]

        # 使用事务确保数据一致性
        with transaction.atomic():
            for data in exercises_data:
                try:
                    self.import_exercise(data)
                    self.stdout.write(self.style.SUCCESS(f"Successfully imported exercise {data['exercise_id']}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error importing exercise {data['exercise_id']}: {str(e)}"))
                    continue

        self.stdout.write(self.style.SUCCESS('All exercises imported successfully'))

    def import_exercise(self, data):
        # 1. 创建或获取外键依赖的实例
        category, _ = Category.objects.get_or_create(category_name=data['category'])
        major, _ = Major.objects.get_or_create(major_name=data['major'], category=category)
        chapter, _ = Chapter.objects.get_or_create(chapter_name=data['chapter'], major=major)
        source, _ = Source.objects.get_or_create(source_name=data['source'])
        exercise_type, _ = ExerciseType.objects.get_or_create(type_name=data['type'])

        # 处理 ExamGroup（允许为空）
        exam_group = None
        if data.get('examgroup'):
            exam_group, _ = ExamGroup.objects.get_or_create(
                examgroup_name=data['examgroup'],
                chapter=chapter
            )

        # 处理 School 和 Exam
        exercise_from_data = data['exerciseFrom']
        school = None
        if exercise_from_data.get('fromSchool'):
            school, _ = School.objects.get_or_create(name=exercise_from_data['fromSchool'])

        exam, _ = Exam.objects.get_or_create(
            category=category,
            school=school,
            from_school=exercise_from_data.get('fromSchool', ''),
            exam_time=exercise_from_data.get('examTime', ''),
            exam_code=exercise_from_data.get('examCode', ''),
            exam_full_name=exercise_from_data.get('examFullName', ''),
        )

        # 2. 创建 Exercise 实例
        exercise, created = Exercise.objects.get_or_create(
            exercise_id=data['exercise_id'],
            defaults={
                'exercise_type': exercise_type,
                'category': category,
                'major': major,
                'chapter': chapter,
                'exam_group': exam_group,
                'source': source,
                'level': data.get('level', 1),  # 默认值为 1
                'score': data.get('score', 0),  # 默认值为 0
            }
        )

        # 3. 创建 ExerciseStem
        stem, _ = ExerciseStem.objects.get_or_create(
            exercise=exercise,
            stem_content=data['stem']
        )
        exercise.stem = stem
        exercise.save()

        # 4. 创建 Question
        for q_data in data.get('questions', []):
            Question.objects.get_or_create(
                exercise=exercise,
                question_order=q_data['questionOrder'],
                defaults={
                    'question_stem': q_data.get('questionStem', ''),
                    'question_answer': q_data['questionAnswer'],
                    'question_analysis': q_data.get('questionAnalysis'),
                }
            )

        # 5. 创建 ExerciseAnswer（最后一个为主答案）
        for ans_data in data.get('answer', []):
            answer, _ = ExerciseAnswer.objects.get_or_create(
                exercise=exercise,
                answer_content=ans_data['answer_content'],
                mark=ans_data['mark'],
                defaults={
                    'from_model': ans_data.get('from_model', ''),
                    'render_type': ans_data.get('render_type', ''),
                }
            )
        # 设置最后一个为主答案
        if data.get('answer'):
            last_answer = data['answer'][-1]
            exercise.answer = ExerciseAnswer.objects.get(
                exercise=exercise,
                answer_content=last_answer['answer_content'],
                mark=last_answer['mark']
            )
            exercise.save()

        # 6. 创建 ExerciseAnalysis（最后一个为主解析）
        for ana_data in data.get('analysis', []):
            analysis, _ = ExerciseAnalysis.objects.get_or_create(
                exercise=exercise,
                analysis_content=ana_data['analysis_content'],
                mark=ana_data['mark'],
                defaults={
                    'render_type': ana_data.get('render_type', ''),
                }
            )
        # 设置最后一个为主解析
        if data.get('analysis'):
            last_analysis = data['analysis'][-1]
            exercise.analysis = ExerciseAnalysis.objects.get(
                exercise=exercise,
                analysis_content=last_analysis['analysis_content'],
                mark=last_analysis['mark']
            )
            exercise.save()

        # 7. 创建 ExerciseFrom
        exercise_from, _ = ExerciseFrom.objects.get_or_create(
            exercise=exercise,
            defaults={
                'exam': exam,
                'is_official_exercise': exercise_from_data.get('isOfficialExercise', 0),
                'exercise_number': exercise_from_data.get('exerciseNumber', 1),
                'material_name': exercise_from_data.get('materialName', ''),
                'section': exercise_from_data.get('section', ''),
                'page_number': exercise_from_data.get('pageNumber', 0),
            }
        )
        exercise.exercise_from = exercise_from
        exercise.save()

        # 8. 创建 ExerciseImage
        for img_data in data.get('image_links', []):
            ExerciseImage.objects.get_or_create(
                exercise=exercise,
                image_link=img_data['image_link'],
                defaults={
                    'source_type': img_data['source_type'],
                    'is_deprecated': img_data['is_deprecated'],
                    'ocr_result': img_data.get('ocr_result', ''),
                }
            )