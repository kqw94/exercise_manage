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

        # 使用事务确保数据一致性，并批量导入
        with transaction.atomic():
            # 预创建外键对象
            categories = self.pre_create_objects(Category, 'category_name', exercises_data, 'category')
            majors = self.pre_create_objects(Major, 'major_name', exercises_data, 'major', category_map=categories)
            chapters = self.pre_create_objects(Chapter, 'chapter_name', exercises_data, 'chapter', major_map=majors)
            exam_groups = self.pre_create_objects(ExamGroup, 'examgroup_name', exercises_data, 'examgroup', chapter_map=chapters, allow_null=True)
            sources = self.pre_create_objects(Source, 'source_name', exercises_data, 'source')
            exercise_types = self.pre_create_objects(ExerciseType, 'type_name', exercises_data, 'type')
            schools = self.pre_create_objects(School, 'name', exercises_data, 'exerciseFrom.fromSchool', allow_null=True)

            exercises_to_create = []
            stems_to_create = []
            questions_to_create = []
            answers_to_create = []
            analyses_to_create = []
            exercise_froms_to_create = []
            images_to_create = []

            for data in exercises_data:
                try:
                    exercise = self.import_exercise(data, categories, majors, chapters, exam_groups, sources, exercise_types, schools,
                                                   exercises_to_create, stems_to_create, questions_to_create, answers_to_create,
                                                   analyses_to_create, exercise_froms_to_create, images_to_create)
                    self.stdout.write(self.style.SUCCESS(f"Imported exercise with new ID {exercise.exercise_id}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error importing exercise: {str(e)}"))
                    continue

            # 批量创建
            Exercise.objects.bulk_create(exercises_to_create, batch_size=1000)
            ExerciseStem.objects.bulk_create(stems_to_create, batch_size=1000)
            Question.objects.bulk_create(questions_to_create, batch_size=1000)
            ExerciseAnswer.objects.bulk_create(answers_to_create, batch_size=1000)
            ExerciseAnalysis.objects.bulk_create(analyses_to_create, batch_size=1000)
            ExerciseFrom.objects.bulk_create(exercise_froms_to_create, batch_size=1000)
            ExerciseImage.objects.bulk_create(images_to_create, batch_size=1000)

            # 更新外键关系
            self.update_foreign_keys(exercises_to_create)

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(exercises_to_create)} exercises'))

    def pre_create_objects(self, model, field_name, data_list, json_key, category_map=None, major_map=None, chapter_map=None, allow_null=False):
        """预创建外键对象并返回映射"""
        existing = {getattr(obj, field_name): obj for obj in model.objects.all()}
        to_create = []
        for data in data_list:
            value = self.get_nested_value(data, json_key)
            if allow_null and (value is None or value == ''):
                continue
            if value and value not in existing:
                obj = model(**{field_name: value})
                if category_map and 'category' in data:
                    obj.category = category_map[data['category']]
                if major_map and 'major' in data:
                    obj.major = major_map[data['major']]
                if chapter_map and 'examgroup' in data and data['examgroup']:
                    obj.chapter = chapter_map[data['chapter']]
                to_create.append(obj)
        if to_create:
            model.objects.bulk_create(to_create)
            existing.update({getattr(obj, field_name): obj for obj in model.objects.filter(**{f'{field_name}__in': [getattr(o, field_name) for o in to_create]})})
        return existing

    def get_nested_value(self, data, key):
        """获取嵌套字段值"""
        keys = key.split('.')
        value = data
        for k in keys:
            value = value.get(k, '') if isinstance(value, dict) else ''
        return value

    def import_exercise(self, data, categories, majors, chapters, exam_groups, sources, exercise_types, schools,
                       exercises_to_create, stems_to_create, questions_to_create, answers_to_create,
                       analyses_to_create, exercise_froms_to_create, images_to_create):
        """创建 Exercise 及其关联对象"""
        # 创建 Exercise（exercise_id 由数据库自增）
        exercise = Exercise(
            exercise_type=exercise_types[data.get('type', '')],
            category=categories[data.get('category', '')],
            major=majors[data.get('major', '')],
            chapter=chapters[data.get('chapter', '')],
            exam_group=exam_groups.get(data.get('examgroup')) if data.get('examgroup') else None,
            source=sources[data.get('source', '')],
            level=data.get('level', 1),
            score=data.get('score', 0)
        )
        exercises_to_create.append(exercise)

        # 创建 ExerciseStem
        if data.get('stem'):
            stems_to_create.append(ExerciseStem(exercise=exercise, stem_content=data['stem']))

        # 创建 Question
        for q_data in data.get('questions', []):
            questions_to_create.append(Question(
                exercise=exercise,
                question_order=q_data.get('questionOrder', 0),
                question_stem=q_data.get('questionStem', ''),
                question_answer=q_data.get('questionAnswer', ''),
                question_analysis=q_data.get('questionAnalysis', '')
            ))

        # 创建 ExerciseAnswer
        for ans_data in data.get('answer', []):
            answers_to_create.append(ExerciseAnswer(
                exercise=exercise,
                answer_content=ans_data.get('answer_content', ''),
                mark=ans_data.get('mark', ''),
                from_model=ans_data.get('from_model', ''),
                render_type=ans_data.get('render_type', '')
            ))

        # 创建 ExerciseAnalysis
        for ana_data in data.get('analysis', []):
            analyses_to_create.append(ExerciseAnalysis(
                exercise=exercise,
                analysis_content=ana_data.get('analysis_content', ''),
                mark=ana_data.get('mark', ''),
                render_type=ana_data.get('render_type', '')
            ))

        # 创建 Exam 和 ExerciseFrom
        exercise_from_data = data.get('exerciseFrom', {})
        school = schools.get(exercise_from_data.get('fromSchool', '')) if exercise_from_data.get('fromSchool') else None
        exam, _ = Exam.objects.get_or_create(
            category=categories[data.get('category', '')],
            school=school,
            from_school=exercise_from_data.get('fromSchool', ''),
            exam_time=exercise_from_data.get('examTime', ''),
            exam_code=exercise_from_data.get('examCode', ''),
            exam_full_name=exercise_from_data.get('examFullName', ''),
        )
        exercise_froms_to_create.append(ExerciseFrom(
            exercise=exercise,
            exam=exam,
            is_official_exercise=exercise_from_data.get('isOfficialExercise', 0),
            exercise_number=exercise_from_data.get('exerciseNumber', 1),
            material_name=exercise_from_data.get('materialName', ''),
            section=exercise_from_data.get('section', ''),
            page_number=exercise_from_data.get('pageNumber', 0)
        ))

        # 创建 ExerciseImage
        for img_data in data.get('image_links', []):
            images_to_create.append(ExerciseImage(
                exercise=exercise,
                image_link=img_data.get('image_link', ''),
                source_type=img_data.get('source_type', 'stem'),
                is_deprecated=img_data.get('is_deprecated', False),
                ocr_result=img_data.get('ocr_result', '')
            ))

        return exercise

    def update_foreign_keys(self, exercises):
        """更新 Exercise 的外键关系"""
        for exercise in exercises:
            if ExerciseStem.objects.filter(exercise=exercise).exists():
                exercise.stem = ExerciseStem.objects.filter(exercise=exercise).first()
            if ExerciseAnswer.objects.filter(exercise=exercise).exists():
                exercise.answer = ExerciseAnswer.objects.filter(exercise=exercise).last()
            if ExerciseAnalysis.objects.filter(exercise=exercise).exists():
                exercise.analysis = ExerciseAnalysis.objects.filter(exercise=exercise).last()
            if ExerciseFrom.objects.filter(exercise=exercise).exists():
                exercise.exercise_from = ExerciseFrom.objects.filter(exercise=exercise).first()
            exercise.save()