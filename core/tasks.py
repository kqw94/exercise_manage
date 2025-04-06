# tasks.py
from celery import shared_task
from core.models import Exercise, Category
import json
from django.core.serializers.json import DjangoJSONEncoder
import os

@shared_task
def export_exercises_by_category(category_id, user_id):
    category = Category.objects.get(category_id=category_id)
    exercises = Exercise.objects.filter(category=category).select_related(
        'exercise_type', 'category', 'major', 'chapter', 'exam_group', 'source', 'stem', 'answer', 'analysis', 'exercise_from'
    ).prefetch_related('questions', 'answers', 'analyses', 'exercise_from__exam', 'exerciseimage_set')

    export_data = []
    for exercise in exercises:
        exercise_data = {
            # 同上，省略具体字段
        }
        export_data.append(exercise_data)

    filename = f"media/exports/exercises_category_{category_id}.json"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, cls=DjangoJSONEncoder)
    return filename