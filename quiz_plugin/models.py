from django.db import models
from django.utils.translation import gettext_lazy as _
from cms.models import CMSPlugin
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _, gettext

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
    text = models.TextField(verbose_name=_("Question Text (HTML)"))
    id_category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=_("Category"))
    
    def __str__(self):
        return f"[{self.id_category.name}] {self.name}"

class Answer(models.Model):
    id = models.AutoField(primary_key=True)
    text = models.TextField(verbose_name=_("Answer Text (HTML)"))
    score = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        verbose_name=_("Score (-1.00 to 1.00)"),
        validators=[MinValueValidator(-1.00), MaxValueValidator(1.00)]
    )
    correction = models.TextField(blank=True, null=True, verbose_name=_("Explanation for incorrect answer (HTML)"))
    id_question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name=_("Question"))

    def __str__(self):
        return f"{self.text[:50]}..." if len(self.text) > 50 else self.text

class Test(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, verbose_name=_("Test Name"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Test Description"))
    min_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00, 
        verbose_name=_("Minimum Passing Score"),
        validators=[MinValueValidator(0.00)]
    )
    questions = models.ManyToManyField(Question, through='QuestionInTest', verbose_name=_("Quizzes in Test"))
    
    def __str__(self):
        return self.name

class QuestionInTest(models.Model):
    id_question = models.ForeignKey(Question, on_delete=models.CASCADE)
    id_test = models.ForeignKey(Test, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0) 

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
    id = models.CharField(primary_key=True, max_length=20, unique=True, verbose_name=_("Execution Code"))
    execution_time = models.DateTimeField(auto_now_add=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    id_sex = models.ForeignKey(Sex, on_delete=models.SET_NULL, null=True, blank=True)
    id_test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    IP = models.GenericIPAddressField(blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    revision_date = models.DateTimeField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Execution {self.id} for Test '{self.id_test.name}'"

class GivenAnswer(models.Model):
    id_testExecution = models.ForeignKey(TestExecution, on_delete=models.CASCADE, related_name='given_answers')
    id_answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    id_question = models.ForeignKey(Question, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('id_testExecution', 'id_question'),)

    def __str__(self):
        return f"Answer in execution {self.id_testExecution_id}"

# CMS Plugin Model
class QuizPluginModel(CMSPlugin):
    def __str__(self):
        return gettext("Quiz Plugin (Random Test)")