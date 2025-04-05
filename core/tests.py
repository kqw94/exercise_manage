from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Category, Major, Chapter, ExamGroup

class CategoryCRUDTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category_data = {'category_name': 'Mathematics'}

    def test_create_category(self):
        response = self.client.post('/api/crud/categories/create/', self.category_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Category.objects.get().category_name, 'Mathematics')

    def test_get_category(self):
        category = Category.objects.create(**self.category_data)
        response = self.client.get(f'/api/crud/categories/{category.category_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['category_name'], 'Mathematics')

    def test_update_category(self):
        category = Category.objects.create(**self.category_data)
        update_data = {'category_name': 'Advanced Mathematics'}
        response = self.client.put(f'/api/crud/categories/{category.category_id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Category.objects.get().category_name, 'Advanced Mathematics')

    def test_delete_category(self):
        category = Category.objects.create(**self.category_data)
        response = self.client.delete(f'/api/crud/categories/{category.category_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)

class MajorCRUDTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(category_name='Mathematics')
        self.major_data = {'major_name': 'Algebra', 'category_id': self.category.category_id}

    def test_create_major(self):
        response = self.client.post('/api/crud/majors/create/', self.major_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Major.objects.count(), 1)
        self.assertEqual(Major.objects.get().major_name, 'Algebra')

    def test_get_major(self):
        major = Major.objects.create(major_name='Algebra', category=self.category)
        response = self.client.get(f'/api/crud/majors/{major.major_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['major_name'], 'Algebra')

    def test_update_major(self):
        major = Major.objects.create(major_name='Algebra', category=self.category)
        update_data = {'major_name': 'Linear Algebra', 'category_id': self.category.category_id}
        response = self.client.put(f'/api/crud/majors/{major.major_id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Major.objects.get().major_name, 'Linear Algebra')

    def test_delete_major(self):
        major = Major.objects.create(major_name='Algebra', category=self.category)
        response = self.client.delete(f'/api/crud/majors/{major.major_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Major.objects.count(), 0)

class ChapterCRUDTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(category_name='Mathematics')
        self.major = Major.objects.create(major_name='Algebra', category=self.category)
        self.chapter_data = {'chapter_name': 'Chapter 1', 'major_id': self.major.major_id}

    def test_create_chapter(self):
        response = self.client.post('/api/crud/chapters/create/', self.chapter_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Chapter.objects.count(), 1)
        self.assertEqual(Chapter.objects.get().chapter_name, 'Chapter 1')

    def test_get_chapter(self):
        chapter = Chapter.objects.create(chapter_name='Chapter 1', major=self.major)
        response = self.client.get(f'/api/crud/chapters/{chapter.chapter_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['chapter_name'], 'Chapter 1')

    def test_update_chapter(self):
        chapter = Chapter.objects.create(chapter_name='Chapter 1', major=self.major)
        update_data = {'chapter_name': 'Chapter 1 Updated', 'major_id': self.major.major_id}
        response = self.client.put(f'/api/crud/chapters/{chapter.chapter_id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Chapter.objects.get().chapter_name, 'Chapter 1 Updated')

    def test_delete_chapter(self):
        chapter = Chapter.objects.create(chapter_name='Chapter 1', major=self.major)
        response = self.client.delete(f'/api/crud/chapters/{chapter.chapter_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Chapter.objects.count(), 0)

class ExamGroupCRUDTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(category_name='Mathematics')
        self.major = Major.objects.create(major_name='Algebra', category=self.category)
        self.chapter = Chapter.objects.create(chapter_name='Chapter 1', major=self.major)
        self.examgroup_data = {'examgroup_name': 'Midterm Exam', 'chapter_id': self.chapter.chapter_id}

    def test_create_examgroup(self):
        response = self.client.post('/api/crud/examgroups/create/', self.examgroup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExamGroup.objects.count(), 1)
        self.assertEqual(ExamGroup.objects.get().examgroup_name, 'Midterm Exam')

    def test_get_examgroup(self):
        examgroup = ExamGroup.objects.create(examgroup_name='Midterm Exam', chapter=self.chapter)
        response = self.client.get(f'/api/crud/examgroups/{examgroup.examgroup_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['examgroup_name'], 'Midterm Exam')

    def test_update_examgroup(self):
        examgroup = ExamGroup.objects.create(examgroup_name='Midterm Exam', chapter=self.chapter)
        update_data = {'examgroup_name': 'Final Exam', 'chapter_id': self.chapter.chapter_id}
        response = self.client.put(f'/api/crud/examgroups/{examgroup.examgroup_id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ExamGroup.objects.get().examgroup_name, 'Final Exam')

    def test_delete_examgroup(self):
        examgroup = ExamGroup.objects.create(examgroup_name='Midterm Exam', chapter=self.chapter)
        response = self.client.delete(f'/api/crud/examgroups/{examgroup.examgroup_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ExamGroup.objects.count(), 0)