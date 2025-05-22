from django.urls import path
from . import views

app_name = 'quiz_plugin'

urlpatterns = [
    # API endpoints
    path('api/sex_options/', views.get_sex_options, name='api_sex_options'),
    path('api/test/<int:test_id>/questions/', views.get_random_test_questions, name='api_test_questions'),
    path('api/submit_results/', views.submit_results, name='api_submit_results'),
    path('api/results/<str:execution_code>/download_pdf/', views.download_quiz_pdf, name='download_quiz_pdf'),
    path('api/random_test_id/', views.get_random_test_id, name='get_random_test_id'),
]