import json
from django.core.management.base import BaseCommand
from core.models import (
    Exercise, ExerciseStem, Question, ExerciseAnswer, ExerciseAnalysis,
    ExerciseFrom, ExerciseImage, Category, Major, Chapter, ExamGroup,
    Source, ExerciseType, Exam
)

class Command(BaseCommand):
    help = 'Load exercise data from JSON file into the database'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')

    def handle(self, *args, **options):
        json_file = options['json_file']

        # 读取 JSON 文件
        with open(json_file, 'r', encoding='utf-8') as f:
            exercises_data = json.load(f)

        # 遍历每个练习题数据
        for data in exercises_data:
            try:
                # 1. 创建或获取外键依赖的实例
                category, _ = Category.objects.get_or_create(category_name=data['category'])
                major, _ = Major.objects.get_or_create(major_name=data['major'], category=category)
                chapter, _ = Chapter.objects.get_or_create(chapter_name=data['chapter'], major=major)
                source, _ = Source.objects.get_or_create(source_name=data['source'])
                exercise_type, _ = ExerciseType.objects.get_or_create(type_name=data['type'])

                # 处理 exam_group（允许为空）
                exam_group = None
                if data['examgroup']:
                    exam_group, _ = ExamGroup.objects.get_or_create(examgroup_name=data['examgroup'], chapter=chapter)

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
                        'level': data['level'],
                        'score': data['score'] or 0,
                    }
                )

                # 3. 创建 ExerciseStem
                stem = ExerciseStem.objects.create(
                    exercise=exercise,
                    stem_content=data['stem']
                )
                exercise.stem = stem
                exercise.save()

                # 4. 创建 Question
                for q_data in data['questions']:
                    Question.objects.create(
                        exercise=exercise,
                        question_order=q_data['questionOrder'],
                        question_stem=q_data['questionStem'],
                        question_answer=q_data['questionAnswer'],
                        question_analysis=q_data['questionAnalysis']
                    )

                # 5. 创建 ExerciseAnswer（最后一个为主答案）
                # 先创建所有非主答案
                for ans_data in data['answer'][:-1]:  # 除了最后一个
                    ExerciseAnswer.objects.create(
                        exercise=exercise,
                        answer_content=ans_data['answer_content'],
                        mark=ans_data['mark'],
                        from_model=ans_data['from_model'],
                        render_type=ans_data['render_type']
                    )
                # 创建最后一个作为主答案
                last_answer = data['answer'][-1]  # 取最后一个答案
                answer = ExerciseAnswer.objects.create(
                    exercise=exercise,
                    answer_content=last_answer['answer_content'],
                    mark=last_answer['mark'],
                    from_model=last_answer['from_model'],
                    render_type=last_answer['render_type']
                )
                exercise.answer = answer
                exercise.save()

                # 6. 创建 ExerciseAnalysis（最后一个为主解析）
                # 先创建所有非主解析
                for ana_data in data['analysis'][:-1]:  # 除了最后一个
                    ExerciseAnalysis.objects.create(
                        exercise=exercise,
                        analysis_content=ana_data['analysis_content'],
                        mark=ana_data['mark'],
                        render_type=ana_data['render_type']
                    )
                # 创建最后一个作为主解析
                last_analysis = data['analysis'][-1]  # 取最后一个解析
                analysis = ExerciseAnalysis.objects.create(
                    exercise=exercise,
                    analysis_content=last_analysis['analysis_content'],
                    mark=last_analysis['mark'],
                    render_type=last_analysis['render_type']
                )
                exercise.analysis = analysis
                exercise.save()

                # 7. 创建 Exam 和 ExerciseFrom
                exam_data = data['exerciseFrom']
                exam, _ = Exam.objects.get_or_create(
                    from_school=exam_data['fromSchool'] or '',
                    exam_time=exam_data['examTime'] or '',
                    exam_code=exam_data['examCode'] or '',
                    exam_full_name=exam_data['examFullName'] or '',
                )
                exercise_from, _ = ExerciseFrom.objects.get_or_create(
                    exercise=exercise,
                    defaults={
                        'exam': exam,
                        'is_official_exercise': exam_data['isOfficialExercise'],
                        'exercise_number': exam_data['exerciseNumber'],
                        'material_name': exam_data['materialName'] or '',
                        'section': exam_data['section'] or '',
                        'page_number': exam_data['pageNumber'],
                    }
                )
                exercise.exercise_from = exercise_from
                exercise.save()

                # 8. 创建 ExerciseImage
                for img_data in data['image_links']:
                    ExerciseImage.objects.create(
                        exercise=exercise,
                        image_link=img_data['image_link'],
                        source_type=img_data['source_type'],
                        is_deprecated=img_data['is_deprecated'],
                        ocr_result=img_data['ocr_result']
                    )

                self.stdout.write(self.style.SUCCESS(f"Successfully loaded exercise {data['exercise_id']}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error loading exercise {data['exercise_id']}: {str(e)}"))
                continue

if __name__ == "__main__":
    # 如果直接运行脚本，可以手动调用（仅用于测试）
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')  # 替换为你的项目 settings 路径
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'load_exercises', 'exercises_0403.json'])