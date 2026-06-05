from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from .models import (
    HomeSlider, Quiz, Question, Choice, 
    QuizAttempt, UserAnswer,AdBanner
)

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    inlines = [ChoiceInline]

@admin.register(HomeSlider)
class HomeSliderAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'order', 'image_url']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['title']

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'is_premium', 'duration_minutes', 'created_at']
    list_editable = ['is_active']
    list_filter = ['is_active', 'is_premium']
    search_fields = ['title', 'password']
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['add_question_url'] = 'add_question/'
        return super().changelist_view(request, extra_context=extra_context)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('add_question/', self.admin_site.admin_view(self.add_question_view), name='quiz_add_question'),
        ]
        return custom_urls + urls
    
    def add_question_view(self, request):
        if request.method == 'POST':
            quiz_id = request.POST.get('quiz_id')
            question_text = request.POST.get('question_text')
            choices = request.POST.getlist('choices[]')
            correct_index = request.POST.get('correct_index')
            
            if quiz_id and question_text and len(choices) >= 2:
                quiz = Quiz.objects.get(id=quiz_id)
                question = Question.objects.create(quiz=quiz, text=question_text, is_active=True)
                
                for i, choice_text in enumerate(choices):
                    Choice.objects.create(
                        question=question,
                        choice_text=choice_text,
                        is_correct=(str(i) == correct_index)
                    )
                
                messages.success(request, 'سوال اضافه شد!')
                return redirect('.')
            
            messages.error(request, 'خطا در اضافه کردن')
        
        quizzes = Quiz.objects.all()
        return render(request, 'admin/quiz_add_question.html', {
            'quizzes': quizzes,
            'title': 'اضافه کردن سوال',
            'opts': self.model._meta,
        })

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'quiz', 'is_active']
    list_filter = ['quiz', 'is_active']
    search_fields = ['text']
    inlines = [ChoiceInline]

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['choice_text', 'question', 'is_correct']
    list_filter = ['is_correct', 'question__quiz']

admin.site.register([QuizAttempt, UserAnswer])

@admin.register(AdBanner)
class AdBannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'position', 'is_active']
    list_filter = ['position', 'is_active']
    list_editable = ['is_active']