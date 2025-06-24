# quiz_plugin/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from cms.models import CMSPlugin
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext

# =============================================================================
# MODELLI DI BASE 
# =============================================================================

class Category(models.Model):
    """
    Rappresenta una categoria per le domande.
    Serve a raggruppare le domande per argomento.
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, verbose_name=_("Category Name"))

    class Meta:
        verbose_name_plural = _("Categories") 
        ordering = ['name'] # Ordina le categorie alfabeticamente di default

    def __str__(self):
        # Rappresentazione testuale dell'oggetto.
        return self.name

class Question(models.Model):
    """
    Rappresenta una singola domanda del quiz.
    Ogni domanda appartiene a una categoria e può avere più risposte (relazione 1-a-N con Answer).
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name=_("Question Name (for internal use)"))
    # Usiamo TextField perché il testo della domanda può essere lungo e contenere HTML.
    text = models.TextField(verbose_name=_("Question Text (HTML)"))
    # ForeignKey crea una relazione "molti-a-uno" con Category.
    # on_delete=models.CASCADE significa che se una categoria viene cancellata,
    # anche tutte le domande associate a essa verranno cancellate.
    id_category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=_("Category"))
    
    def __str__(self):
        return f"[{self.id_category.name}] {self.name}"

class Answer(models.Model):
    """
    Rappresenta una possibile risposta a una domanda.
    Ogni risposta è legata a una sola domanda.
    """
    id = models.AutoField(primary_key=True)
    text = models.TextField(verbose_name=_("Answer Text (HTML)"))
    score = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        verbose_name=_("Score (-1.00 to 1.00)"),
        # I validatori assicurano che nessuno possa inserire un punteggio non valido.
        validators=[MinValueValidator(-1.00), MaxValueValidator(1.00)]
    )
    # Spiegazione da mostrare se l'utente sceglie questa risposta e non è corretta.
    # blank=True, null=True significa che questo campo non è obbligatorio.
    correction = models.TextField(blank=True, null=True, verbose_name=_("Explanation for incorrect answer (HTML)"))
    # `related_name='answers'` permette di accedere a tutte le risposte di una domanda
    # in modo intuitivo (es. `question.answers.all()`).
    id_question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name=_("Question"))

    def __str__(self):
        # Mostra solo i primi 50 caratteri per non affollare l'admin.
        return f"{self.text[:50]}..." if len(self.text) > 50 else self.text


# =============================================================================
# MODELLI PER I TEST
# =============================================================================

class Test(models.Model):
    """
    Rappresenta un "Test", che è un insieme ordinato di domande (Quiz).
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, verbose_name=_("Test Name"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Test Description"))
    min_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00, 
        verbose_name=_("Minimum Passing Score")
    )
    # Questa è una relazione "molti-a-molti". Un test può avere molte domande,
    # e una domanda può essere in molti test.
    questions = models.ManyToManyField(Question, verbose_name=_("Quizzes in Test"))
    
    def __str__(self):
        return self.name


# =============================================================================
# MODELLI PER L'ESECUZIONE E I RISULTATI (Dati generati dagli utenti)
# =============================================================================

class Sex(models.Model):
    """
    Modello per memorizzare le opzioni per il sesso.
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Sex Description"))

    class Meta:
        verbose_name_plural = _("Sex Options")

    def __str__(self):
        return self.name

class TestExecution(models.Model):
    """
    Registra una singola esecuzione di un test da parte di un utente.
    Contiene i dati personali, il punteggio finale e le informazioni sulla revisione medica.
    """
    #CharField per il codice univoco perché contiene lettere e numeri.
    id = models.CharField(primary_key=True, max_length=20, unique=True, verbose_name=_("Execution Code"))
    # auto_now_add=True imposta automaticamente la data e l'ora alla creazione dell'oggetto.
    execution_time = models.DateTimeField(auto_now_add=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    # on_delete=models.SET_NULL: se un'opzione di sesso viene cancellata, il campo in questa
    # esecuzione diventa NULL, ma l'esecuzione non viene cancellata.
    id_sex = models.ForeignKey(Sex, on_delete=models.SET_NULL, null=True, blank=True)
    id_test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    # GenericIPAddressField è il campo specifico di Django per indirizzi IP.
    IP = models.GenericIPAddressField(blank=True, null=True)
    # DurationField è perfetto per memorizzare intervalli di tempo, come la durata di un test.
    duration = models.DurationField(blank=True, null=True)


    # Campi per la revisione da parte del medico
    revision_date = models.DateTimeField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    # ForeignKey al modello User standard di Django.
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Execution {self.id} for Test '{self.id_test.name}'"

class GivenAnswer(models.Model):
    """
    Registra quale risposta specifica è stata data a una domanda
    all'interno di una determinata esecuzione di un test.
    """
    # related_name='given_answers' ci permette di fare `test_execution.given_answers.all()`
    id_testExecution = models.ForeignKey(TestExecution, on_delete=models.CASCADE, related_name='given_answers')
    id_answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    id_question = models.ForeignKey(Question, on_delete=models.CASCADE)

    class Meta:
        # Impedisce che un utente possa dare due risposte alla stessa domanda nello stesso test.
        unique_together = (('id_testExecution', 'id_question'),)

    def __str__(self):
        return f"Answer in execution {self.id_testExecution_id}"

# =============================================================================
# MODELLO PER IL PLUGIN DI DJANGO-CMS
# =============================================================================

class QuizPluginModel(CMSPlugin):
    """
    Modello che permette di inserire il quiz come un plugin in una pagina di Django-CMS.
    Eredita da CMSPlugin.
    """
    def __str__(self):
        # Testo mostrato nell'interfaccia di Django-CMS per identificare il plugin.
        return gettext("Quiz Plugin (Random Test)")