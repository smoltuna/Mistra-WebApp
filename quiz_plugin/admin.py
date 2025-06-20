# quiz_plugin/admin.py

from django import forms
from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# 1. Importa il widget dell'editor di testo da djangocms-text-ckeditor
from djangocms_text_ckeditor.widgets import TextEditorWidget

from .models import Test, Question, Answer, Category, Sex, QuestionInTest, TestExecution, User

# ===================================================================
# FORMS PERSONALIZZATE CON EDITOR WYSIWYG
# Queste form sostituiscono i campi di testo standard con un editor HTML.
# ===================================================================

class TestAdminForm(forms.ModelForm):
    # Applica il widget al campo 'description'
    description = forms.CharField(
        widget=TextEditorWidget(), 
        required=False, 
        label=_("Test Description (HTML)")
    )
    class Meta:
        model = Test
        fields = '__all__'

class AnswerAdminForm(forms.ModelForm):
    # Applica il widget ai campi 'text' e 'correction'
    text = forms.CharField(widget=TextEditorWidget(), label=_("Answer Text (HTML)"))
    correction = forms.CharField(
        widget=TextEditorWidget(), 
        required=False, 
        label=_("Explanation for incorrect answer (HTML)")
    )
    class Meta:
        model = Answer
        fields = '__all__'

class QuestionAdminForm(forms.ModelForm):
    # Applica il widget anche al testo della domanda
    text = forms.CharField(widget=TextEditorWidget(), label=_("Question Text (HTML)"))
    class Meta:
        model = Question
        fields = '__all__'


# ===================================================================
# CONFIGURAZIONI ADMIN
# ===================================================================

class QuestionInTestInline(admin.TabularInline):
    model = QuestionInTest
    extra = 1
    autocomplete_fields = ['id_question']
    exclude = ('order',)

class AnswerInline(admin.TabularInline):
    # Usa la form personalizzata per l'editor HTML
    form = AnswerAdminForm
    model = Answer
    extra = 1

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    # Applica la form personalizzata all'admin di Test
    form = TestAdminForm
    list_display = ('name', 'min_score')
    search_fields = ('name', 'description')
    inlines = [QuestionInTestInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    # Applica la form personalizzata all'admin di Question
    form = QuestionAdminForm
    list_display = ('name', 'id_category')
    list_filter = ('id_category',)
    search_fields = ('name', 'text',)
    inlines = [AnswerInline]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Sex)
class SexAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(TestExecution)
class TestExecutionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'id_test', 'execution_time', 'age', 'id_sex', 'score',
        'duration', 'get_revision_date_display', 'get_reviewed_by_full_name'
    )
    list_filter = ('id_test', 'id_sex', 'execution_time', 'reviewed_by')
    search_fields = ('id', 'IP', 'reviewed_by__username')
    autocomplete_fields = ['id_test']

    readonly_fields = (
        'id', 'execution_time', 'IP', 'duration', 'score',
        'age', 'id_sex', 'id_test', # id_test è readonly perché legato all'esecuzione
        'get_revision_date_display', 'get_reviewed_by_full_name'
    )

    fieldsets = (
        (_('Execution Details'), {
            'fields': ('id', 'execution_time', 'IP', 'duration', 'score')
        }),
        (_('Test and User Information'), {
            'fields': ('id_test', 'age', 'id_sex')
        }),
        (_('Medical Revision'), {
            'fields': ('note', 'get_revision_date_display', 'get_reviewed_by_full_name')
        }),
    )

    def get_reviewed_by_full_name(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name() or obj.reviewed_by.username
        return "N/A"
    get_reviewed_by_full_name.short_description = _("Reviewed By")

    def get_revision_date_display(self, obj):
        if obj.revision_date:
            return timezone.localtime(obj.revision_date).strftime('%d/%m/%Y %H:%M')
        return "N/A"
    get_revision_date_display.short_description = _("Revision Date")

    def save_model(self, request, obj, form, change):
        # Se la nota viene modificata, aggiorna l'utente e la data della revisione
        if 'note' in form.changed_data:
            obj.reviewed_by = request.user
            obj.revision_date = timezone.now()
        super().save_model(request, obj, form, change)