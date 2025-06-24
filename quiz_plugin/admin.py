from django import forms
from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


#editor HTML
from djangocms_text_ckeditor.widgets import TextEditorWidget

#Modelli necessari per registrarli nell'admin.
from .models import Test, Question, Answer, Category, Sex, QuestionInTest, TestExecution, User


# L'admin di Django di default usa un semplice <textarea> per i campi di testo.
# Insieme alle classi `ModelForm` permettono di diventare editor HTML (TextEditorWidget)".

class TestAdminForm(forms.ModelForm):
    # Sovrascriviamo il campo 'description' del modello Test.
    description = forms.CharField(
        widget=TextEditorWidget(),  # Applica l'editor HTML.
        required=False,            
        label=_("Test Description (HTML)")
    )
    class Meta:
        model = Test
        fields = '__all__' # Applica la modifica a tutti i campi del modello.

class AnswerAdminForm(forms.ModelForm):
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
    text = forms.CharField(widget=TextEditorWidget(), label=_("Question Text (HTML)"))
    class Meta:
        model = Question
        fields = '__all__'

# ===================================================================
# CONFIGURAZIONI ADMIN
# ===================================================================
# Qui registriamo i modelli per renderli visibili e gestibili nell'interfaccia
# di amministrazione di Django, personalizzandone l'aspetto e il comportamento.

# Gli "inlines" permettono di modificare modelli correlati direttamente dalla pagina
# del modello principale. Es: modificare le risposte di una domanda dalla pagina della domanda.

class QuestionInTestInline(admin.TabularInline):
    """Permette di aggiungere/rimuovere domande a un Test direttamente dalla pagina del Test."""
    model = QuestionInTest  # Il modello della tabella intermedia.
    extra = 1  # Mostra uno slot vuoto per aggiungere una nuova domanda.
    autocomplete_fields = ['id_question'] # Trasforma il menu a tendina delle domande in un campo di ricerca (utile se hai molte domande).
    exclude = ('order',) # Esclude il campo 'order' dalla modifica manuale (potrebbe essere gestito automaticamente).

class AnswerInline(admin.TabularInline):
    """Permette di aggiungere/modificare le risposte di una Domanda direttamente dalla pagina della Domanda."""
    form = AnswerAdminForm # Form personalizzata con l'editor HTML.
    model = Answer
    extra = 1

# --- REGISTRAZIONE DEI MODELLI PRINCIPALI ---

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    """Personalizzazione dell'interfaccia admin per il modello Test."""
    form = TestAdminForm  # Applica la form con l'editor HTML per la descrizione.
    list_display = ('name', 'min_score') # Colonne da mostrare nella lista dei test.
    search_fields = ('name', 'description') # Abilita la ricerca per nome e descrizione.
    inlines = [QuestionInTestInline] # Aggiunge l'inline per gestire le domande.

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Personalizzazione dell'interfaccia admin per il modello Question."""
    form = QuestionAdminForm # Applica la form con l'editor HTML per il testo della domanda.
    list_display = ('name', 'id_category') # Colonne da mostrare nella lista.
    list_filter = ('id_category',) # Aggiunge un filtro sulla destra per categoria.
    search_fields = ('name', 'text',)
    inlines = [AnswerInline] # Aggiunge l'inline per gestire le risposte.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Sex)
class SexAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(TestExecution)
class TestExecutionAdmin(admin.ModelAdmin):
    """Personalizzazione dell'interfaccia admin per le esecuzioni dei test (la più complessa)."""
    # Colonne da mostrare nella lista delle esecuzioni.
    list_display = (
        'id', 'id_test', 'execution_time', 'age', 'id_sex', 'score',
        'duration', 'get_revision_date_display', 'get_reviewed_by_full_name'
    )
    list_filter = ('id_test', 'id_sex', 'execution_time', 'reviewed_by')
    search_fields = ('id', 'IP', 'reviewed_by__username')
    autocomplete_fields = ['id_test']

    # Campi che non possono essere modificati manualmente dall'admin (sono calcolati o automatici).
    readonly_fields = (
        'id', 'execution_time', 'IP', 'duration', 'score', 'age', 'id_sex', 'id_test',
        'get_revision_date_display', 'get_reviewed_by_full_name'
    )

    # Raggruppa i campi in sezioni (fieldset) per una migliore organizzazione nella pagina di dettaglio.
    fieldsets = (
        (_('Execution Details'), {'fields': ('id', 'execution_time', 'IP', 'duration', 'score')}),
        (_('Test and User Information'), {'fields': ('id_test', 'age', 'id_sex')}),
        (_('Medical Revision'), {'fields': ('note', 'get_revision_date_display', 'get_reviewed_by_full_name')}),
    )

    # --- METODI PERSONALIZZATI ---
    # Questi metodi creano delle "colonne calcolate" per la `list_display` o campi in `readonly_fields`.

    def get_reviewed_by_full_name(self, obj):
        """Restituisce il nome completo dell'utente che ha revisionato, o il suo username."""
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name() or obj.reviewed_by.username
        return "N/A"
    get_reviewed_by_full_name.short_description = _("Reviewed By") # Etichetta della colonna.

    def get_revision_date_display(self, obj):
        """Formatta la data di revisione."""
        if obj.revision_date:
            return timezone.localtime(obj.revision_date).strftime('%d/%m/%Y %H:%M')
        return "N/A"
    get_revision_date_display.short_description = _("Revision Date")

    def save_model(self, request, obj, form, change):
        """
        Sovrascrive il metodo di salvataggio standard di Django per aggiungere logica personalizzata.
        In questo caso, se il medico modifica il campo 'note', registriamo automaticamente
        chi ha fatto la modifica (`request.user`) e quando (`timezone.now()`).
        """
        if 'note' in form.changed_data:
            obj.reviewed_by = request.user
            obj.revision_date = timezone.now()
        super().save_model(request, obj, form, change)