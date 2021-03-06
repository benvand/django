from __future__ import unicode_literals

import string

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.db.models.signals import pre_save, pre_delete
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.sites import get_site_model
SiteModel = get_site_model()

SITE_CACHE = {}


def _simple_domain_name_validator(value):
    """
    Validates that the given value contains no whitespaces to prevent common
    typos.
    """
    if not value:
        return
    checks = ((s in value) for s in string.whitespace)
    if any(checks):
        raise ValidationError(
            _("The domain name cannot contain any spaces or tabs."),
            code='invalid',
        )


class SiteManager(models.Manager):

    def get_current(self):
        """
        Returns the current ``Site`` based on the SITE_ID in the
        project's settings. The ``Site`` object is cached the first
        time it's retrieved from the database.
        """
        from django.conf import settings
        try:
            sid = settings.SITE_ID
        except AttributeError:
            raise ImproperlyConfigured(
                "You're using the Django \"sites framework\" without having "
                "set the SITE_ID setting. Create a site in your database and "
                "set the SITE_ID setting to fix this error.")
        try:
            current_site = SITE_CACHE[sid]
        except KeyError:
            current_site = self.get(pk=sid)
            SITE_CACHE[sid] = current_site
        return current_site

    def clear_cache(self):
        """Clears the ``Site`` object cache."""
        global SITE_CACHE
        SITE_CACHE = {}


@python_2_unicode_compatible
class AbstractBaseSite(models.Model):
    """
    This is the bare minimum that a site should have
    """
    domain = models.CharField(_('domain name'), max_length=100,
        validators=[_simple_domain_name_validator])
    name = models.CharField(_('display name'), max_length=50)

    objects = SiteManager()

    def __str__(self):
        return self.domain

    class Meta:
        abstract = True

class AbstractSite(AbstractBaseSite):
    """
    An abstract base class to allow for the customization of the
    sites model used to create site through inheritance of this model
    """

    # class Meta(AbstractBaseSite.Meta):
    #     db_table = 'django_site'
    #     verbose_name = _('site')
    #     verbose_name_plural = _('sites')
    #     ordering = ('domain',)

class Site(AbstractSite):
    """
    Sites using the default 'django.contrib.sites' are represented by this model
    domain and name are required.
    """
    class Meta(AbstractSite.Meta):
        swappable = 'SITE_MODEL'

@python_2_unicode_compatible
class RequestSite(object):
    """
    A class that shares the primary interface of Site (i.e., it has
    ``domain`` and ``name`` attributes) but gets its data from a Django
    HttpRequest object rather than from a database.

    The save() and delete() methods raise NotImplementedError.
    """
    def __init__(self, request):
        self.domain = self.name = request.get_host()

    def __str__(self):
        return self.domain

    def save(self, force_insert=False, force_update=False):
        raise NotImplementedError('RequestSite cannot be saved.')

    def delete(self):
        raise NotImplementedError('RequestSite cannot be deleted.')


def get_current_site(request):
    """
    Checks if contrib.sites is installed and returns either the current
    ``Site`` object or a ``RequestSite`` object based on the request.
    """
    if SiteModel._meta.installed:
        current_site = SiteModel.objects.get_current()
    else:
        current_site = RequestSite(request)
    return current_site


def clear_site_cache(sender, **kwargs):
    """
    Clears the cache (if primed) each time a site is saved or deleted
    """
    instance = kwargs['instance']
    try:
        del SITE_CACHE[instance.pk]
    except KeyError:
        pass
pre_save.connect(clear_site_cache, sender=Site)
pre_delete.connect(clear_site_cache, sender=Site)
