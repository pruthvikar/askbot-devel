from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache
from askbot.deps.livesettings import ConfigurationSettings, forms
from askbot.deps.livesettings import ImageValue
from askbot.deps.livesettings.overrides import get_overrides
from django.contrib import messages
import logging
from django import forms as dforms
from django.db import models
from django.forms import ModelForm
from askbot.models import user
from django.forms.models import modelformset_factory
from django.shortcuts import get_object_or_404

#temporary model, swap to final model when done
class SpaceManager(models.Manager):
    def create_space(self, name,description):
        space = self.create(name=name,description=description)
        return space

class Space(models.Model):
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=20)
    objects=SpaceManager()
    def __unicode__(self):
        return self.name

class SelectForm(dforms.Form):
    Create_or_Edit_Space = dforms.ModelChoiceField(empty_label='New Space...',queryset = Space.objects.all(),required=False,widget=dforms.Select(attrs={'size':'15','onChange':'this.form.submit()','method':'post'}))

class SpaceForm(ModelForm):
    

    class Meta:
        
        model=Space
        fields=['name','description']

log = logging.getLogger('configuration.views')

def spaces_settings(request, template='livesettings/space_settings.html'):
    use_db, overrides = get_overrides();
    
    mgr = ConfigurationSettings()
    settings = mgr['SPACE']

    if use_db:
        if request.method=='GET' and request.GET.get('Create_or_Edit_Space'):
            
            try :
                instance=Space.objects.get(pk=request.GET['Create_or_Edit_Space'])
                selectform=SelectForm(initial = {'Create_or_Edit_Space': instance.pk })
                thisform=SpaceForm(instance=instance)

            except KeyError:
                selectform=SelectForm(initial = {'Create_or_Edit_Space': 0 })
                thisform=SpaceForm()
        
        elif request.method=='POST':
            if request.GET['Create_or_Edit_Space']:
                instance=Space.objects.get(pk=request.GET['Create_or_Edit_Space'])
                selectform=SelectForm(initial={'Create_or_Edit_Space': instance.pk })
            else:
                instance=None
                selectform=SelectForm(initial = {'Create_or_Edit_Space': 0 })
            
            
            thisform=SpaceForm(request.POST,request.FILES,instance=instance)
                
            if thisform.is_valid():
                thisform.save()
        else:
            thisform=SpaceForm()
            selectform=SelectForm()
                            
    else:
        form = None

    return render_to_response(template, {
                              'all_super_groups': mgr.get_super_groups(),
                              'group' : settings,
                              'select':selectform,
                              'form': thisform,
                              'use_db' : use_db
                              }, context_instance=RequestContext(request))


def group_settings(request, group, template='livesettings/group_settings.html'):
    # Determine what set of settings this editor is used for
    
    use_db, overrides = get_overrides();
    
    mgr = ConfigurationSettings()
    
    settings = mgr[group]

    
    if use_db:
        # Create an editor customized for the current user
        #editor = forms.customized_editor(settings)
        
        if request.method == 'POST':
            
            # Populate the form with user-submitted data
            data = request.POST.copy()
            form = forms.SettingsEditor(data, request.FILES, settings=settings)
            if form.is_valid():
                for name, value in form.cleaned_data.items():
                    group, key = name.split('__')
                    cfg = mgr.get_config(group, key)
                    
                    if isinstance(cfg, ImageValue):
                        if request.FILES and name in request.FILES:
                            value = request.FILES[name]
                        else:
                            continue
                    
                    try:
                        cfg.update(value)
                    #message='Updated %s on %s' % (cfg.key, cfg.group.key)
                    #messages.success(request, message)
                    #the else if for the settings that are not updated.
                    except Exception, e:
                        request.user.message_set.create(message=e.message)
                
                return HttpResponseRedirect(request.path)
        else:
            # Leave the form populated with current setting values
            #form = editor()
            form = forms.SettingsEditor(settings=settings)
    else:
        form = None
    
    return render_to_response(template, {
                              'all_super_groups': mgr.get_super_groups(),
                              'group' : settings,
                              'form': form,
                              'use_db' : use_db
                              }, context_instance=RequestContext(request))
group_settings = never_cache(staff_member_required(group_settings))

# Site-wide setting editor is identical, but without a group
# staff_member_required is implied, since it calls group_settings
def site_settings(request):
    mgr = ConfigurationSettings()
    default_group= mgr.groups()[0].key
    return HttpResponseRedirect(reverse('group_settings', args=[default_group]))
#return group_settings(request, group=None, template='livesettings/site_settings.html')

def export_as_python(request):
    """Export site settings as a dictionary of dictionaries"""
    
    from askbot.deps.livesettings.models import Setting, LongSetting
    import pprint
    
    work = {}
    both = list(Setting.objects.all())
    both.extend(list(LongSetting.objects.all()))
    
    for s in both:
        if not work.has_key(s.site.id):
            work[s.site.id] = {}
        sitesettings = work[s.site.id]
        
        if not sitesettings.has_key(s.group):
            sitesettings[s.group] = {}
        sitegroup = sitesettings[s.group]
        
        sitegroup[s.key] = s.value
    
    pp = pprint.PrettyPrinter(indent=4)
    pretty = pp.pformat(work)
    
    return render_to_response('livesettings/text.txt', { 'text' : pretty }, mimetype='text/plain')

export_as_python = never_cache(staff_member_required(export_as_python))
