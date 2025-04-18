from django.urls import path
from .views import (
    CategoryList, MajorListByCategory, ChapterListByMajor, ExamGroupListByChapter,
    ExerciseList, AnswerListByExercise, AnalysisListByExercise, ExerciseTypeList, SourceList, BulkExerciseUpdate,
    ExamSchoolList, ExamTimeList, ExamCodeList, ExamFullNameList, ExamList, ExamDetail,
    # 新增的 CRUD 视图
    CategoryCreate, CategoryDetail, MajorCreate, MajorDetail, SchoolList, SchoolDetail,
    ChapterCreate, ChapterDetail, ExamGroupCreate, ExamGroupDetail, ExamSchoolListByCategoryId,
    RegisterView, LoginView, LogoutView, UserListView, UserDetailView, RoleListView, 
    RoleDetailView, RolePermissionListView, RolePermissionDetailView, UserActionLogListView,
    InitializeRolesView, ExportExercisesByCategoryView, ImportExercisesView,
    BulkExerciseCreateView, UserActionLogDeleteView, ExportExercisesView, RefreshTokenView
)

urlpatterns = [
    # 登录注册
    
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),

    # 用户管理
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),

    # 角色管理
    path('roles/', RoleListView.as_view(), name='role_list'),
    path('roles/<int:pk>/', RoleDetailView.as_view(), name='role_detail'),

    # 角色权限管理
    path('role-permissions/', RolePermissionListView.as_view(), name='role_permission_list'),
    path('role-permissions/<int:pk>/', RolePermissionDetailView.as_view(), name='role_permission_detail'),
    # --- 已有路由保持不变 ---
    # 显示所有 Category
    path('categories/', CategoryList.as_view(), name='category-list'),
    # 根据 category_id 获取 major 列表
    path('majors/<int:category_id>/', MajorListByCategory.as_view(), name='major-list-by-category'),
    # 根据 major_id 获取 chapter 列表
    path('chapters/<int:major_id>/', ChapterListByMajor.as_view(), name='chapter-list-by-major'),
    # 根据 chapter_id 获取 examgroup 列表
    path('examgroups/<int:chapter_id>/', ExamGroupListByChapter.as_view(), name='examgroup-list-by-chapter'),
    # 根据 category/major/chapter/examgroup 获取 exercise 列表
    path('exercises/', ExerciseList.as_view(), name='exercise-list'),
    path('exercises/<str:exercise_id>/', ExerciseList.as_view(), name='exercise-detail'),  # 支持 PUT
    # 根据 exercise_id 获取答案列表
    path('answers/<str:exercise_id>/', AnswerListByExercise.as_view(), name='answer-list-by-exercise'),
    # 根据 exercise_id 获取解析列表
    path('analyses/<str:exercise_id>/', AnalysisListByExercise.as_view(), name='analysis-list-by-exercise'),
    # 其他已有路由
    path('exercise-types/', ExerciseTypeList.as_view(), name='exercise-type-list'),
    path('sources/', SourceList.as_view(), name='source-list'),
    path('timu/bulk-update/', BulkExerciseUpdate.as_view(), name='bulk-exercise-update'),
    
    # School 路由
    path('schools/', SchoolList.as_view(), name='school-list'),
    path('schools/<int:pk>/', SchoolDetail.as_view(), name='school-detail'),
    
    path('exams/', ExamList.as_view(), name='exam-list'),
    path('exam-schools/', ExamSchoolList.as_view(), name='exam-school-list'),
    path('exam-schools-list/', ExamSchoolListByCategoryId.as_view(), name='exam-school-list-by-category'),
    path('exam-times/<str:exam_school>/', ExamTimeList.as_view(), name='exam-time-list'),
    path('exam-codes/<str:exam_school>/<str:exam_time>/', ExamCodeList.as_view(), name='exam-code-list'),
    path('exam-full-names/<str:exam_school>/<str:exam_time>/<str:exam_code>/', ExamFullNameList.as_view(), name='exam-full-name-list'),

    # --- 新增 CRUD 路由（添加 /crud/ 前缀避免冲突） ---
    path('crud/categories/create/', CategoryCreate.as_view(), name='crud-category-create'),
    path('crud/categories/<int:category_id>/', CategoryDetail.as_view(), name='crud-category-detail'),
    path('crud/majors/create/', MajorCreate.as_view(), name='crud-major-create'),
    path('crud/majors/<int:major_id>/', MajorDetail.as_view(), name='crud-major-detail'),
    path('crud/chapters/create/', ChapterCreate.as_view(), name='crud-chapter-create'),
    path('crud/chapters/<int:chapter_id>/', ChapterDetail.as_view(), name='crud-chapter-detail'),
    path('crud/examgroups/create/', ExamGroupCreate.as_view(), name='crud-examgroup-create'),
    path('crud/examgroups/<int:examgroup_id>/', ExamGroupDetail.as_view(), name='crud-examgroup-detail'),

    path('initialize-roles/', InitializeRolesView.as_view(), name='initialize_roles'),

    path('export-exercises-by-category/<int:category_id>/', ExportExercisesByCategoryView.as_view(), name='export-exercises-by-category'),
    path('export-exercises/', ExportExercisesView.as_view(), name='export-exercises'),
    
    path('import-exercises/', ImportExercisesView.as_view(), name='import_exercises'),
    path('exercises/bulk/', BulkExerciseCreateView.as_view(), name='bulk-exercise-create'),
    path('user-action-logs/', UserActionLogListView.as_view(), name='user-action-log-list'),
    path('user-action-logs/<int:id>/', UserActionLogDeleteView.as_view(), name='user-action-log-delete'),

]