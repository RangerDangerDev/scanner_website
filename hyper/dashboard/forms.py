from django import forms
from .models import asset, port_info, asset_group
class ScanForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name'}))
    scan_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scan Name'}))
    address = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'EX: 192.168.1.1, 192.168.1.10-192.168.1.15, 192.168.2.0/24'}))
    ports = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '22'}))
    def __init__(self, user, *args, **kwargs):
        super(ScanForm, self).__init__(*args,**kwargs)
        self.fields['asset_groups'] = forms.MultipleChoiceField(
            choices = [(group['name'], group['name']) for group in asset_group.objects.filter(user=user).values('name').distinct()],
            )
        self.fields['asset_groups'].widget.attrs.update({'class':'select2 form-control select2-multiple', 'data-toggle' : 'select2', 'multiple' : 'multiple'})
class RenameScanForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'New Name'}))

class CreateAssetGroup(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'New Name'}))



class AddAssetForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super(AddAssetForm, self).__init__(*args,**kwargs)
        self.fields['Add Addresses'] = forms.MultipleChoiceField(
            choices=[(ip['ip'], ip['ip']) for ip in port_info.objects.filter(user=user).values('ip').distinct()],
        )
        self.fields['Add Addresses'].widget.attrs.update({'class':'select2 form-control select2-multiple', 'data-toggle' : 'select2', 'multiple' : 'multiple'})

class DeleteAssetForm(forms.Form):
    def __init__(self, user,groupid, *args, **kwargs):
        super(DeleteAssetForm, self).__init__(*args,**kwargs)
        self.fields['Remove Addresses'] = forms.MultipleChoiceField(
            choices=[(ip['address'], ip['address']) for ip in asset.objects.filter(user=user, group=groupid).values('address').distinct()],
        )
        self.fields['Remove Addresses'].widget.attrs.update({'class':'select2 form-control select2-multiple', 'data-toggle' : 'select2', 'multiple' : 'multiple'})