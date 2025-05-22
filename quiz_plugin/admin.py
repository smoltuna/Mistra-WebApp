from django.contrib import admin
from .models import Category, Question, Answer, Test, QuestionInTest, Sex, TestExecution, GivenAnswer

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ('texto', 'score', 'correction')
    # Use formfield_for_foreignkey to customize widgets if needed for HTML fields

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('name', 'id_category')
    list_filter = ('id_category',)
    search_fields = ('name', 'texto')
    inlines = [AnswerInline]
    # For HTML fields, you might want to integrate a rich text editor in the admin.
    # This often requires custom form widgets or third-party packages (e.g., django-ckeditor).

admin.site.register(Category)
admin.site.register(Question, QuestionAdmin)

class QuestionInTestInline(admin.TabularInline):
    model = QuestionInTest
    extra = 1
    fields = ('id_question', 'order')
    raw_id_fields = ('id_question',) # Use raw_id_fields for large number of questions for performance

class TestAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_score')
    search_fields = ('name', 'description')
    inlines = [QuestionInTestInline]
    # Allow filtering questions by category when adding to a test (more advanced, may require custom form or JS)
    # This might require overriding the form for the Test model or using custom JavaScript in the admin.

admin.site.register(Test, TestAdmin)
admin.site.register(Sex)

class GivenAnswerInline(admin.TabularInline):
    model = GivenAnswer
    extra = 0
    can_delete = False
    readonly_fields = ('id_answer', 'id_question') # Display given answers

@admin.register(TestExecution)
class TestExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_test', 'execution_time', 'score', 'age', 'id_sex', 'revision_date')
    list_filter = ('id_test', 'id_sex', 'revision_date')
    search_fields = ('id', 'IP', 'note')
    readonly_fields = ('id', 'execution_time', 'age', 'id_sex', 'id_test', 'score', 'IP', 'duration')
    inlines = [GivenAnswerInline]
    actions = ['mark_as_reviewed']

    def mark_as_reviewed(self, request, queryset):
        # Action to add revision date and allow adding a note
        for obj in queryset:
            # You'd need a form or modal to capture the 'note' here.
            # For simplicity, let's just update the date for now.
            obj.revision_date = timezone.now()
            obj.save()
        self.message_user(request, "Selected tests marked as reviewed.")
    mark_as_reviewed.short_description = "Mark selected tests as reviewed"