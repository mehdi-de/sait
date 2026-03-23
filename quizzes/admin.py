from django.contrib import admin
from .models import Quiz, Question, Choice, QuizAttempt,UserAnswer

# --- Inline برای Choice ---
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    fields = ('choice_text', 'is_correct')

# --- Inline برای Question ---
class QuestionInline(admin.TabularInline):
    model = Question
    show_change_link = True
    fields = ('text', 'is_active')
    extra = 10

# --- Admin Question ---
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'get_correct_choice', 'is_active')
    list_filter = ('quiz', 'is_active')
    search_fields = ('text',)
    inlines = [ChoiceInline]

    def get_correct_choice(self, obj):
        correct = obj.choices.filter(is_correct=True).first()
        return correct.choice_text if correct else "تعیین نشده"
    get_correct_choice.short_description = "گزینه صحیح"

# --- Admin Quiz ---
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'total_questions', 'is_premium')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]

    def total_questions(self, obj):
        return obj.questions.count()
    total_questions.short_description = "تعداد سوالات"

# --- Admin QuizAttempt ---
@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'started_at', 'is_completed', 'score')
    list_filter = ('quiz', 'is_completed', 'started_at')
    search_fields = ('user__username', 'quiz__title')


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_choice')
    list_filter = ('attempt',)


