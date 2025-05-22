# mistra/urls.py
from cms.sitemaps import CMSSitemap
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

admin.autodiscover()

# These are your project-level URLs that typically do NOT need internationalization
urlpatterns = [
    path('admin/', admin.site.urls), # Admin generally doesn't need to be internationalized
    path("sitemap.xml", sitemap, {"sitemaps": {"cmspages": CMSSitemap}}),
    # path('quiz/', include('quiz_plugin.urls')), # Your custom quiz app URLs
]

# These are the internationalized URL patterns.
# All Django CMS pages should be accessed with a language prefix (e.g., /en/contatti/)
urlpatterns += i18n_patterns(
    path("quiz/", include("quiz_plugin.urls")),
    path("", include("cms.urls")), # This handles all CMS pages (e.g., /en/contatti/)
    # You can add other localized patterns here if needed,
    # but typically, cms.urls is sufficient for page routing.
    # For example, if you had an 'about' app that was localized:
    # path("about/", include("about_app.urls")),
    prefix_default_language=True, # Optional: if you want '/' to redirect to '/en/' for default language
)

# This is only needed when using runserver.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)