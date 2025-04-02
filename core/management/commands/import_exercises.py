import json
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import (
    Category, Major, Chapter, ExamGroup, ExerciseType, Source, Exam,
    Exercise, ExerciseStem, Question, ExerciseAnswer, ExerciseAnalysis,
    ExerciseFrom, ExerciseProperty, KnowledgeTag, ExerciseKnowledgeTag,
    ExerciseImage, ExerciseOcrResult
)

class Command(BaseCommand):
    help = 'Import exercises from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')

    def handle(self, *args, **options):
        json_file = options['json_file']
        with open(json_file, 'r', encoding='utf-8') as f:
            exercises_data = json.load(f)

        # 使用事务分批处理，提高性能
        batch_size = 1000
        total = len(exercises_data)
        for i in range(0, total, batch_size):
            batch = exercises_data[i:i + batch_size]
            with transaction.atomic():
                for data in batch:
                    # 1. Category (专业)
                    category, _ = Category.objects.get_or_create(category_name='默认专业')

                    # 2. Major (科目)
                    major, _ = Major.objects.get_or_create(
                        major_name=data['majorName'],
                        category=category
                    )

                    # 3. Chapter (章节)
                    chapter, _ = Chapter.objects.get_or_create(
                        chapter_name=data['chapterName'],
                        major=major
                    )

                    # 4. ExamGroup (考点)
                    exam_group, _ = ExamGroup.objects.get_or_create(
                        examgroup_name=data['examgroupName'],
                        chapter=chapter
                    )

                    # 5. ExerciseType (题目类型)
                    exercise_type, _ = ExerciseType.objects.get_or_create(
                        type_name=data['exerciseType']
                    )

                    # 6. Source (来源)
                    source, _ = Source.objects.get_or_create(
                        source_name=data['source']
                    )

                    # 7. Exam (考试信息)
                    exam_data = data['exerciseFrom']
                    exam, _ = Exam.objects.get_or_create(
                        from_school=exam_data['fromSchool'],
                        exam_time=exam_data['examTime'],
                        exam_code=exam_data['examCode'],
                        exam_full_name=exam_data['examFullName']
                    )

                    # 8. Exercise (题目)
                    exercise, created = Exercise.objects.get_or_create(
                        exercise_id=data['exerciseId'],
                        defaults={
                            'exercise_type': exercise_type,
                            'exam_group': exam_group,
                            'source': source,
                        }
                    )
    
                    if created:
                        # 9. ExerciseStem (题干)
                        ExerciseStem.objects.create(
                            exercise=exercise,
                            stem_content=data['exerciseStems']
                        )

                        # 10. Questions (选项)
                        for q in data['questions']:
                            Question.objects.create(
                                exercise=exercise,
                                question_order=q['questionOrder'],
                                question_stem=q['questionStem'],
                                question_answer=q['questionAnswer'],
                                question_analysis=q['questionAnalysis'] if q['questionAnalysis'] != 'None' else None
                            )

                        # 11. ExerciseAnswer (答案)
                        ExerciseAnswer.objects.create(
                            exercise=exercise,
                            answer=data['exerciseAnswer'],
                            answer_ds=data.get('answerDs', ''),
                            answer_gpt=data.get('answerGpt', ''),
                            answer_proofread=data.get('answerProofread', ''),
                            answer_quality_check=data.get('answerQualityCheck', '')
                        )

                        # 12. ExerciseAnalysis (解析)
                        ExerciseAnalysis.objects.create(
                            exercise=exercise,
                            analysis=data['exerciseAnalysis'],
                            analysis_ds=data.get('analysisDs', ''),
                            analysis_gpt=data.get('analysisGpt', ''),
                            analysis_proofread=data.get('analysisProofread', ''),
                            analysis_quality_check=data.get('analysisQualityCheck', '')
                        )

                        # 13. ExerciseFrom (题目来源)
                        ExerciseFrom.objects.create(
                            exercise=exercise,
                            exam=exam,
                            is_official_exercise=exam_data['isOfficialExercise'],
                            exercise_number=exam_data['exerciseNumber'],
                            material_name=exam_data['materialName'],
                            section=exam_data['section'],
                            page_number=exam_data['pageNumber'] if exam_data['pageNumber'] is not None else None
                        )

                        # 14. ExerciseProperty (题目属性)
                        prop = data['exerciseProperty']
                        ExerciseProperty.objects.create(
                            exercise=exercise,
                            level=prop['level'],
                            score=prop['score']
                        )

                        # 15. KnowledgeTags (知识标签)
                        if prop['knowledgeTags']:
                            for tag_id in prop['knowledgeTags'][0].split(','):
                                tag, _ = KnowledgeTag.objects.get_or_create(
                                    tag_id=tag_id,
                                    defaults={'tag_name': f'知识点_{tag_id}'}
                                )
                                ExerciseKnowledgeTag.objects.get_or_create(
                                    exercise=exercise,
                                    tag=tag
                                )

                        # 16. ExerciseImages (图片链接)
                        img_links = data['imgLinks']
                        for img_type, links in img_links.items():
                            for link in links:
                                ExerciseImage.objects.create(
                                    exercise=exercise,
                                    image_type=img_type.replace('ImgLink', ''),
                                    image_link=link
                                )

                        # 17. ExerciseOcrResults (OCR结果)
                        ocr_res = data['ocrRes']
                        for ocr_type, results in ocr_res.items():
                            for result in results:
                                ExerciseOcrResult.objects.create(
                                    exercise=exercise,
                                    ocr_type=ocr_type.replace('OcrRes', ''),
                                    ocr_result=result
                                )

            self.stdout.write(self.style.SUCCESS(f'Imported {i + len(batch)} of {total} exercises'))

        self.stdout.write(self.style.SUCCESS(f'Successfully imported all {total} exercises'))