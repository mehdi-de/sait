from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages

from .models import (
    HomeSlider,
    Quiz,
    Question,
    Choice,
    QuizAttempt,
    UserAnswer,
    AdBanner,
    VisitorStats,
    IPVisit,
)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'quiz', 'is_active']
    list_filter = ['quiz', 'is_active']
    search_fields = ['text']
    inlines = [ChoiceInline]


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'is_active',
        'is_premium',
        'duration_minutes',
        'created_at',
    ]

    list_filter = ['is_active', 'is_premium']
    list_editable = ['is_active']
    search_fields = ['title']

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                'add-question/',
                self.admin_site.admin_view(self.add_question_view),
                name='quiz_add_question',
            ),
        ]

        return custom_urls + urls

    def add_question_view(self, request):

        if request.method == 'POST':

            quiz_id = request.POST.get('quiz_id')
            question_text = request.POST.get('question_text')
            choices = request.POST.getlist('choices[]')
            correct_index = request.POST.get('correct_index')

            if quiz_id and question_text and len(choices) >= 2:

                try:
                    quiz = Quiz.objects.get(id=quiz_id)

                    question = Question.objects.create(
                        quiz=quiz,
                        text=question_text,
                        is_active=True,
                    )

                    for index, choice_text in enumerate(choices):

                        if choice_text.strip():
                            Choice.objects.create(
                                question=question,
                                choice_text=choice_text,
                                is_correct=(str(index) == correct_index),
                            )

                    messages.success(request, 'سوال با موفقیت اضافه شد.')
                    return redirect('../')

                except Quiz.DoesNotExist:
                    messages.error(request, 'آزمون پیدا نشد.')

            else:
                messages.error(request, 'اطلاعات ناقص است.')

        quizzes = Quiz.objects.all()

        context = {
            'quizzes': quizzes,
            'title': 'افزودن سوال',
            'opts': self.model._meta,
        }

        return render(request, 'admin/quiz_add_question.html', context)


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['choice_text', 'question', 'is_correct']
    list_filter = ['is_correct']
    search_fields = ['choice_text']


@admin.register(HomeSlider)
class HomeSliderAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'order', 'image_url']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['title']


@admin.register(AdBanner)
class AdBannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'position', 'is_active']
    list_editable = ['is_active']
    list_filter = ['position', 'is_active']


@admin.register(VisitorStats)
class VisitorStatsAdmin(admin.ModelAdmin):
    list_display = ['date', 'unique_visitors_today']
    ordering = ['-date']


@admin.register(IPVisit)
class IPVisitAdmin(admin.ModelAdmin):
    list_display = ['ip_address', 'date', 'created_at']
    ordering = ['-created_at']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'quiz',
        'score',
        'is_completed',
        'started_at',
    ]

    list_filter = ['is_completed']
    search_fields = ['user__username', 'quiz__title']


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'selected_choice']