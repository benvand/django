from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model, get_app

def format_app_model(settingsvalue):
    try:
        app_label, model_name = getattr(settings,settingsvalue).split('.')
    except ValueError:
        raise ImproperlyConfigured(
            "%s must be of the form 'app_label.model_name'" % settingsvalue)
    return app_label, model_name


def get_site_model():
    #TODO: This is a carbon copy of get_user_model in auth.__init__
    #Abstract out this method so it can be passed an app name
    # eg get_model('site') or get_model('user')
    #  not get_user_model() get_site_model()
    #Look at django.db.models.loading.Cache
    """
    Returns the Site model that is active in this project.
    """
    app_label, model_name = format_app_model('SITE_MODEL')
    site_model = get_model(app_label, model_name)
    if site_model is None:
        raise ImproperlyConfigured("SITE_MODEL refers to model '%s' that has not been installed" % settings.SITE_MODEL)
    return site_model

def get_site_app():
    app_label, model_name = format_app_model('SITE_MODEL')
    app = get_app(app_label)
    if app is None:
        raise ImproperlyConfigured("SITE_MODEL refers to app '%s' that has not been installed" % app_label)
    elif app_label not in settings.INSTALLED_APPS:
        raise ImproperlyConfigured("""SITE_MODEL refers to app '%s' that
            is not in settings.INSTALLED_APPS""" % settings.AUTH_USER_MODEL)
    return app