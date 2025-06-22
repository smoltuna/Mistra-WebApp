from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import gettext_lazy as _
from .models import QuizPluginModel, Test 

@plugin_pool.register_plugin
class QuizPluginPublisher(CMSPluginBase):
    model = QuizPluginModel 
    name = _("Quiz Plugin (Random Test)")
    render_template = "quiz_plugin/quiz_plugin.html" 
    cache = False

    def render(self, context, instance, placeholder):
        # context = super().render(context, instance, placeholder)
        # context['test_instance'] = instance.test
        return context