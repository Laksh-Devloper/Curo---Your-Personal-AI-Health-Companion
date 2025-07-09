from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_room, name='chat_room'),  # Matches 'chat_room'
    path('generate_health_report/', views.generate_health_report, name='generate_health_report'),
     path('mark_todo_done/<int:todo_id>/', views.mark_todo_done, name='mark_todo_done'),
    path('clear_completed_todos/', views.clear_completed_todos, name='clear_completed_todos'),
]