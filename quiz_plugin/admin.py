# your_app_name/admin.py

from django.contrib import admin
from django.utils import timezone
from django.contrib.auth.models import Group # Non usato direttamente nel codice fornito, ma spesso utile
from django.utils.translation import gettext_lazy as _

# Importa tutti i modelli dal file models.py
# Ho commentato QuizPluginModel e GivenAnswer perché erano commentati anche nel tuo codice originale.
from .models import Test, Question, Answer, Category, Sex, QuestionInTest, TestExecution # , GivenAnswer, QuizPluginModel
from django.contrib.auth.models import User

# Inline per QuestionInTest, per gestirle direttamente dalla pagina del Test
class QuestionInTestInline(admin.TabularInline):
    model = QuestionInTest
    extra = 1
    # Se 'order' è un campo automatico o non deve essere modificato direttamente nell'inline,
    # puoi mantenerlo escluso. Se invece deve essere visibile e modificabile, rimuovi 'exclude'.
    # Lo commento qui per renderlo potenzialmente modificabile o visibile se necessario.
    exclude = ('order',)

    # CORREZIONE PRINCIPALE: Usa 'id_question' che è il nome del campo ForeignKey nel tuo modello QuestionInTest
    autocomplete_fields = ['id_question'] # <-- CAMBIATO DA 'question' A 'id_question'

    # Se avevi raw_id_fields per 'id_question', questo è l'equivalente moderno e più user-friendly
    # raw_id_fields = ('id_question',) # Rimuovi o commenta questa riga se usi autocomplete_fields

# Inline per Answer, per gestirle direttamente dalla pagina della Question
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ('text', 'score', 'correction')


# Registrazione del modello Test nell'amministrazione di Django
@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'min_score')
    search_fields = ('name', 'description')
    inlines = [QuestionInTestInline]

# Registrazione del modello Question nell'amministrazione di Django
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    # 'name' come primo campo per display in QuestionAdmin se esiste e vuoi usarlo per l'autocomplete
    # Se 'name' non è presente nel modello Question, usa 'text' come primo campo.
    # E assicurati che il metodo __str__ di Question restituisca 'text' o 'name'.
    list_display = ('name', 'id_category', 'text') # Assicurati che 'name' esista nel modello Question
    list_filter = ('id_category',)
    search_fields = ('name', 'text',) # Aggiunto 'name' per la ricerca
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

    # Aggiungi id_test a autocomplete_fields se vuoi un campo di autocompletamento per il Test
    autocomplete_fields = ['id_test'] # Aggiunto per migliorare l'usabilità del campo id_test

    readonly_fields = (
        'id', 'execution_time', 'IP', 'duration', 'score',
        'age', 'id_sex',
        'get_revision_date_display', 'get_reviewed_by_full_name'
    )

    # Rimosso id_test dai readonly_fields se è un campo di autocompletamento modificabile
    # Se id_test deve essere readonly (non modificabile dopo la creazione), rimuovilo da autocomplete_fields
    # e lascialo in readonly_fields. Per coerenza con il "sostituisci ricerca per id", lo rendiamo modificabile.
    # Se il test è sempre readonly in TestExecution, allora 'id_test' dovrebbe rimanere in readonly_fields
    # e non in autocomplete_fields. Valuta tu se l'ID del test è modificabile o meno in un'esecuzione.

    fieldsets = (
        (None, {
            'fields': (
                ('id', 'execution_time'),
                # Rimosso id_test da qui se è in autocomplete_fields e non readonly
                ('score'),
                ('IP', 'duration'),
            )
        }),
        (_('Test Information'), { # Rinominato per chiarezza
            'fields': (
                ('id_test',), # Aggiunto qui il campo id_test se è in autocomplete_fields
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

    # raw_id_fields = ('id_test',) # Rimosso, sostituito da autocomplete_fields

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
        # Solo se l'oggetto è nuovo o il campo reviewed_by non è stato impostato
        # altrimenti potrebbe sovrascrivere una revisione manuale.
        # Questa logica dipende da come vuoi che funzioni la revisione.
        if not obj.pk or not obj.reviewed_by: # Se è un nuovo oggetto o non è stato ancora revisionato
            if request.user.is_authenticated:
                obj.reviewed_by = request.user
                obj.revision_date = timezone.now()
        super().save_model(request, obj, form, change)


# Registrazione del modello GivenAnswer nell'amministrazione di Django (COMMENTATO - se hai bisogno, decommenta e configura)
# @admin.register(GivenAnswer)
# class GivenAnswerAdmin(admin.ModelAdmin):
#     list_display = ('id_testExecution', 'id_question', 'id_answer')
#     list_filter = ('id_testExecution__id_test', 'id_question')
#     # Assumi che questi campi siano ForeignKey nel modello GivenAnswer
#     autocomplete_fields = ('id_testExecution', 'id_question', 'id_answer') # Aggiunto autocomplete
#     # raw_id_fields = ('id_testExecution', 'id_question', 'id_answer') # Rimosso

# CMS Plugin Model (COMMENTATO - se hai bisogno, decommenta e configura)
# @admin.register(QuizPluginModel)
# class QuizPluginModelAdmin(admin.ModelAdmin):
#     list_display = ('__str__',)