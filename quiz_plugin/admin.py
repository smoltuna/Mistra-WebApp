# your_app_name/admin.py

from django.contrib import admin
from django.utils import timezone
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

# Importa tutti i modelli dal file models.py
from .models import Test, Question, Answer, Category, Sex, QuestionInTest, TestExecution, GivenAnswer, QuizPluginModel
from django.contrib.auth.models import User # Importa il modello User di Django, se non è già importato da .models

# Inline per QuestionInTest, per gestirle direttamente dalla pagina del Test
class QuestionInTestInline(admin.TabularInline):
    model = QuestionInTest
    extra = 1
    exclude = ('order',)
    raw_id_fields = ('id_question',)

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

# Registrazione del modello Answer nell'amministrazione di Django
@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('texto', 'id_question', 'score', 'correction')
    list_filter = ('id_question__id_category', 'id_question')
    search_fields = ('texto', 'id_question__texto')
    raw_id_fields = ('id_question',)

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
        'duration', 'get_revision_date_display', 'get_reviewed_by_full_name' # Usa il metodo personalizzato
    )
    list_filter = ('id_test', 'id_sex', 'execution_time', 'reviewed_by')
    search_fields = ('id', 'IP', 'reviewed_by__first_name', 'reviewed_by__last_name', 'reviewed_by__username')

    # Tutti questi campi saranno visualizzati ma non modificabili direttamente nel form.
    readonly_fields = (
        'id', 'execution_time', 'IP', 'duration', 'score',
        'age', 'id_sex', 'id_test',
        'get_revision_date_display', 'get_reviewed_by_full_name' # Usa il metodo personalizzato
    )

    # Definisci l'organizzazione dei campi nel modulo di amministrazione
    fieldsets = (
        (None, { # Sezione principale (senza titolo visibile)
            'fields': (
                ('id', 'execution_time'), # ID e Timestamp sulla stessa riga
                ('id_test', 'score'),     # Test e Punteggio sulla stessa riga
                ('IP', 'duration'),       # IP e Durata sulla stessa riga
            )
        }),
        (_('User Information'), { # Sezione per i dati utente
            'fields': (
                ('age', 'id_sex'), # Età e Sesso sulla stessa riga
            )
        }),
        (_('Medical Revision Details'), { # Sezione per i dettagli della revisione medica
            'fields': (
                'get_revision_date_display', # Usa il metodo personalizzato
                'get_reviewed_by_full_name',   # Usa il metodo personalizzato
                'note'           # Nota su una riga separata
            ),
            'description': _('These fields are updated automatically when a medical professional saves the record.')
        }),
    )

    raw_id_fields = ('id_test',)

    # Aggiungi opzioni per migliorare la navigazione e la visualizzazione della lista
    list_per_page = 25 # Numero di elementi per pagina nella lista
    date_hierarchy = 'execution_time' # Permette di navigare per data (es. anno, mese, giorno)
    ordering = ('-execution_time',) # Ordine predefinito: dal più recente al più vecchio

    # Metodo per ottenere il nome completo del medico revisore
    def get_reviewed_by_full_name(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name()
        return "Reviewed By: N/A" # Revertito a inglese

    get_reviewed_by_full_name.short_description = "Reviewed By" # Revertito a inglese e accorciato

    # Metodo per visualizzare la data di revisione con un'etichetta più breve
    def get_revision_date_display(self, obj):
        if obj.revision_date:
            # Formatta la data e l'ora per una visualizzazione più chiara
            return timezone.localtime(obj.revision_date).strftime('%d/%m/%Y %H:%M')
        return "Revision Date: N/A" # Revertito a inglese

    get_revision_date_display.short_description = "Revision Date" # Revertito a inglese e accorciato


    def save_model(self, request, obj, form, change):
        if request.user.is_authenticated:
            obj.reviewed_by = request.user
            obj.revision_date = timezone.now()

        super().save_model(request, obj, form, change)


# Registrazione del modello GivenAnswer nell'amministrazione di Django
@admin.register(GivenAnswer)
class GivenAnswerAdmin(admin.ModelAdmin):
    list_display = ('id_testExecution', 'id_question', 'id_answer')
    list_filter = ('id_testExecution__id_test', 'id_question')
    raw_id_fields = ('id_testExecution', 'id_question', 'id_answer')

# CMS Plugin Model
@admin.register(QuizPluginModel) # Registra QuizPluginModel nell'admin
class QuizPluginModelAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
