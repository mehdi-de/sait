from django.contrib import admin
from .models import (
    HomeSlider, Quiz, Question, Choice, 
    QuizAttempt, UserAnswer
)

# اسلایدر
@admin.register(HomeSlider)
class HomeSliderAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'order', 'image_url']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['title']

# آزمون
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_premium', 'duration_minutes', 'created_at']
    list_filter = ['is_premium']
    search_fields = ['title', 'password']

# سوال
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'quiz', 'is_active']
    list_filter = ['quiz', 'is_active']
    search_fields = ['text']

# گزینه
@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['choice_text', 'question', 'is_correct']
    list_filter = ['is_correct', 'question__quiz']

# بقیه مدل‌ها (ساده)
admin.site.register([QuizAttempt, UserAnswer])