# your_app_name/admin.py

from django.contrib import admin
from django.utils import timezone
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

# Importa tutti i modelli dal file models.py
from .models import Test, Question, Answer, Category, Sex, QuestionInTest, TestExecution, GivenAnswer, QuizPluginModel
from django.contrib.auth.models import User 

# Inline per QuestionInTest, per gestirle direttamente dalla pagina del Test
class QuestionInTestInline(admin.TabularInline):
    model = QuestionInTest
    extra = 1
    exclude = ('order',)
    raw_id_fields = ('id_question',)

# Inline per Answer, per gestirle direttamente dalla pagina della Question
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ('texto', 'score', 'correction')


# Registrazione del modello Test nell'amministrazione di Django
@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'min_score')
    search_fields = ('name', 'description')
    inlines = [QuestionInTestInline]

# Registrazione del modello Question nell'amministrazione di Django
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('name', 'id_category', 'texto')
    list_filter = ('id_category',)
    search_fields = ('name', 'texto')
    inlines = [AnswerInline]

# Registrazione del modello Category nell'amministrazione di Django
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# Registrazione del modello Sex nell'amministrazione di Django
@admin.register(Sex)
class SexAdmin(admin.ModelAdmin):
    list_display = ('name',)

# Registrazione del modello TestExecution nell'amministrazione di Django
@admin.register(TestExecution)
class TestExecutionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'id_test', 'execution_time', 'age', 'id_sex', 'score',
        'duration', 'get_revision_date_display', 'get_reviewed_by_full_name'
    )
    list_filter = ('id_test', 'id_sex', 'execution_time', 'reviewed_by')
    search_fields = ('id', 'IP', 'reviewed_by__first_name', 'reviewed_by__last_name', 'reviewed_by__username')

    readonly_fields = (
        'id', 'execution_time', 'IP', 'duration', 'score',
        'age', 'id_sex', 'id_test',
        'get_revision_date_display', 'get_reviewed_by_full_name'
    )

    fieldsets = (
        (None, {
            'fields': (
                ('id', 'execution_time'),
                ('id_test', 'score'),
                ('IP', 'duration'),
            )
        }),
        (_('User Information'), {
            'fields': (
                ('age', 'id_sex'),
            )
        }),
        (_('Medical Revision Details'), {
            'fields': (
                'get_revision_date_display',
                'get_reviewed_by_full_name',
                'note'
            ),
            'description': _('These fields are updated automatically when a medical professional saves the record.')
        }),
    )

    raw_id_fields = ('id_test',)

    list_per_page = 25
    date_hierarchy = 'execution_time'
    ordering = ('-execution_time',)

    def get_reviewed_by_full_name(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name()
        return "Reviewed By: N/A"

    get_reviewed_by_full_name.short_description = "Reviewed By"

    def get_revision_date_display(self, obj):
        if obj.revision_date:
            return timezone.localtime(obj.revision_date).strftime('%d/%m/%Y %H:%M')
        return "Revision Date: N/A"

    get_revision_date_display.short_description = "Revision Date"


    def save_model(self, request, obj, form, change):
        if request.user.is_authenticated:
            obj.reviewed_by = request.user
            obj.revision_date = timezone.now()

        super().save_model(request, obj, form, change)


# Registrazione del modello GivenAnswer nell'amministrazione di Django (COMMENTATO)
# @admin.register(GivenAnswer)
# class GivenAnswerAdmin(admin.ModelAdmin):
#     list_display = ('id_testExecution', 'id_question', 'id_answer')
#     list_filter = ('id_testExecution__id_test', 'id_question')
#     raw_id_fields = ('id_testExecution', 'id_question', 'id_answer')

# CMS Plugin Model (COMMENTATO)
# @admin.register(QuizPluginModel)
# class QuizPluginModelAdmin(admin.ModelAdmin):
#     list_display = ('__str__',)