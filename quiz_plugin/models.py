from django.db import models
from django.utils.translation import gettext_lazy as _
from cms.models import CMSPlugin
import uuid # For unique execution codes

class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, verbose_name=_("Category Name"))

    class Meta:
        verbose_name_plural = _("Categories")
        ordering = ['name']

    def __str__(self):
        return self.name

class Question(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name=_("Question Name (for internal use)"))
    texto = models.TextField(verbose_name=_("Question Text (HTML)"))
    id_category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=_("Category"))

    # class Meta:
    #     managed = False
    #     db_table = 'Question'
    
    def __str__(self):
        return f"{self.name} - {self.texto}"

class Answer(models.Model):
    id = models.AutoField(primary_key=True)
    texto = models.TextField(verbose_name=_("Answer Text (HTML)"))
    score = models.DecimalField(max_digits=3, decimal_places=2, verbose_name=_("Score (-1.00 to 1.00)")) # -1, 0, 1
    correction = models.TextField(blank=True, null=True, verbose_name=_("Explanation for incorrect answer (HTML)"))
    id_question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name=_("Question"))

    # class Meta:
    #     managed = False
    #     db_table = 'Answer'

    def __str__(self):
        return f"{self.texto[:50]}..." if len(self.texto) > 50 else self.texto

class Test(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, verbose_name=_("Test Name"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Test Description"))
    min_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name=_("Minimum Passing Score"))
    questions = models.ManyToManyField(Question, through='QuestionInTest', verbose_name=_("Quizzes in Test"))

    def __str__(self):
        return self.name

class QuestionInTest(models.Model):
    id_question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name=_("Question"))
    id_test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name=_("Test"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order in Test")) # To define sequence

    class Meta:
        unique_together = ('id_question', 'id_test')
        ordering = ['order']

    def __str__(self):
        return f"{self.id_question.name} in {self.id_test.name}"

class Sex(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Sex Description"))

    class Meta:
        verbose_name_plural = _("Sex Options")

    def __str__(self):
        return self.name

class TestExecution(models.Model):
    id = models.CharField(primary_key=True, max_length=20, unique=True, verbose_name=_("Execution Code")) # e.g., date + 3 letters
    execution_time = models.DateTimeField(auto_now_add=True, verbose_name=_("Execution Timestamp"))
    age = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("User Age"))
    id_sex = models.ForeignKey(Sex, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("User Sex"))
    id_test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name=_("Test Performed"))
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name=_("Total Score"))
    IP = models.GenericIPAddressField(blank=True, null=True, verbose_name=_("User IP Address"))
    duration = models.DurationField(blank=True, null=True, verbose_name=_("Duration (minutes)")) # Stored as timedelta, can be converted to minutes
    revision_date = models.DateTimeField(blank=True, null=True, verbose_name=_("Revision Date by Medical Professional"))
    note = models.TextField(blank=True, null=True, verbose_name=_("Medical Professional's Note"))

    def generate_execution_code(self):
        # Example: YYYYMMDD + 3 random uppercase letters
        today = models.DateTimeField(auto_now_add=True).strftime('%Y%m%d')
        random_letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        return f"{today}{random_letters}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self.generate_execution_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Execution {self.id} for Test '{self.id_test.name}'"

class GivenAnswer(models.Model):
    # Removed db_column for id_testExecution (as fixed previously)
    id_testExecution = models.ForeignKey(
        TestExecution,
        on_delete=models.CASCADE,
        related_name='given_answers'
    )
    # REMOVED db_column='id_answer' here
    # Django will default to 'id_answer_id' for the column name,
    # which is what the database is likely using based on the error.
    id_answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='given_in_executions'
    )
    id_question = models.ForeignKey( # This field was added in previous step
        Question,
        on_delete=models.CASCADE,
        related_name='given_answers_for_question',
    )


    class Meta:
        # managed = False
        # db_table = 'GivenAnswer'
        unique_together = (('id_testExecution', 'id_question'),) # More appropriate unique constraint if one answer per question per execution

    def __str__(self):
        return ""
        # return f"Given answer for Q: '{self.id_question.texto[:30]}...' A: '{self.id_answer.texto[:30]}...' (Execution: {self.id_testExecution.id})"


# CMS Plugin Model
class QuizPluginModel(CMSPlugin):
    # test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name=_("Select Test"))

    def __str__(self):
        return f"Quiz Plugin (Random Test)"