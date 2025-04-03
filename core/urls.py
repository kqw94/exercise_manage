# core/urls.py
from django.urls import path
from .views import (
    CategoryList, MajorListByCategory, ChapterListByMajor, ExamGroupListByChapter,
    ExerciseList, AnswerListByExercise, AnalysisListByExercise
)

urlpatterns = [
    # 新增：显示所有 Category
    path('categories/', CategoryList.as_view(), name='category-list'),
    # 1. 根据 category_id 获取 major 列表
    path('majors/<int:category_id>/', MajorListByCategory.as_view(), name='major-list-by-category'),
    # 2. 根据 major_id 获取 chapter 列表
    path('chapters/<int:major_id>/', ChapterListByMajor.as_view(), name='chapter-list-by-major'),
    # 3. 根据 chapter_id 获取 examgroup 列表
    path('examgroups/<int:chapter_id>/', ExamGroupListByChapter.as_view(), name='examgroup-list-by-chapter'),
    # 4. 根据 category/major/chapter/examgroup 获取 exercise 列表
    path('exercises/', ExerciseList.as_view(), name='exercise-list'),
    # 5. 根据 exercise_id 获取答案列表
    path('answers/<str:exercise_id>/', AnswerListByExercise.as_view(), name='answer-list-by-exercise'),
    # 6. 根据 exercise_id 获取解析列表
    path('analyses/<str:exercise_id>/', AnalysisListByExercise.as_view(), name='analysis-list-by-exercise'),
]