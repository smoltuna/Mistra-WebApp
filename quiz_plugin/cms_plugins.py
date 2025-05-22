# quiz_plugin/cms_plugins.py
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import gettext_lazy as _
from .models import QuizPluginModel, Test # Ensure this import is correct

@plugin_pool.register_plugin
class QuizPluginPublisher(CMSPluginBase):
    model = QuizPluginModel # Your plugin model
    name = _("Quiz Plugin (Random Test)")
    render_template = "quiz_plugin/quiz_plugin.html" # Double-check this path if your app is 'quiz_plugin'
    cache = False

    def render(self, context, instance, placeholder):
        # context = super().render(context, instance, placeholder)
        # context['test_instance'] = instance.test
        return context