from askbot.conf.settings_wrapper import settings
from askbot.conf.super_groups import LOGIN_USERS_COMMUNICATION
from askbot.deps import livesettings
from django.utils.translation import ugettext_lazy as _

SPACE = livesettings.ConfigurationGroup(
                    'SPACE',
                    _('Spaces control settings'),
                    super_group = LOGIN_USERS_COMMUNICATION
                )
settings.register(
                  livesettings.LongStringValue(
                                               SPACE,
                                               'PLACEHOLDER',
                                               default='',
                                               description=_('This is added so space appears in the left menu'),
                                               help_text=_('Remove when fixed')
                                               )
                  )
