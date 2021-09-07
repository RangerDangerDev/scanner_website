from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import TemplateView
from .forms import ScanForm, RenameScanForm, CreateAssetGroup, AddAssetForm
from hyper.utils.general import *
from .tasks import go_to_sleep
from django.shortcuts import redirect


User = get_user_model()
class LoginRequiredView(LoginRequiredMixin, TemplateView):
    pass


class DashboardMainView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/main.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scans = select_scans(self.request.user.id)
        context['cve_nums'] = num_cves(self.request.user.id)
        context['scans'] = scans
        context['scan_num'] = len(scans)
        return context


class ScanDetailsView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/scan/scan_details.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['slug'] = self.kwargs['slug']
        selected_scan = select_slug(self.kwargs['slug'][5:],self.request.user.id)
        context['scan'] = selected_scan
        if len(selected_scan) >= 1:
            context['data'] = get_scan_data(self.kwargs['slug'][5:], self.request.user.id)
        return context   
class CveDetailsView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/scan/cve_details.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scan_id = self.kwargs['slug']
        cve_id = self.kwargs['cveid']
        context['cve'] = get_cve(scan_id[5:],cve_id,self.request.user.id)
        return context

class ScanView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/scan/scan.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['scan_form'] = ScanForm()
        return context
    def post(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        form = ScanForm(request.POST)
        if form.is_valid():
            context['name'] = form.cleaned_data['name']
            context['address'] = clense_ips(form.cleaned_data['address'])
            context['scan_name'] = form.cleaned_data['scan_name']
            slug = add_scan(request.user.id, form.cleaned_data['scan_name'],", ".join(clense_ips(form.cleaned_data['address'])))
            context['task_id'] = convert_scan_to_model(form.cleaned_data['name'], slug[5:])
            

        return self.render_to_response(context)

class ScanManageView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/scan/scan_manage.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['slug'] = self.kwargs['slug']
        context['rename_form'] = RenameScanForm()
        return context

    def post(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        form = RenameScanForm(request.POST)
        if form.is_valid():
            context['new_name'] = form.cleaned_data['name']
            scan = select_slug(self.kwargs['slug'][5:], request.user.id)
            scan.update(name=form.cleaned_data['name'])
            
            return redirect(f"/scan/{self.kwargs['slug']}")
        if request.POST.get('delete'):
            clear_ports(request.user.id, self.kwargs['slug'][5:])
            clear_scans(request.user.id, self.kwargs['slug'][5:])
            return redirect('/')
        return self.render_to_response(context)


class AddressDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/address/address_dashboard.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ip_list = get_ips(user=self.request.user.id)
        context['ip_list'] = []
        for ip in ip_list:
            context['ip_list'].append([ip, ip.replace('.', '-')])
        return context
class AddressDetailsView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/address/address_details.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs['slug'].replace('-', '.')
        context['data'] = get_address_data(self.request.user.id, slug)
        return context
class AddressCveDetailsView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/scan/cve_details.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        address = self.kwargs['slug'].replace('-', '.')
        cve_id = self.kwargs['cveid']
        context['cve'] = get_address_cve(address, self.request.user.id, cve_id)
        return context
class AssetGroupDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/assets/assets.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data'] = []
        groups = get_asset_groups(user=self.request.user.id)
        for group in groups:
            context['data'].append([group, get_assets(self.request.user.id, group)])
        return context


class CreateAssetGroupView(LoginRequiredMixin, TemplateView):
    template_name ="dashboard/assets/create.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_form'] = CreateAssetGroup()
        return context
    def post(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        form = CreateAssetGroup(request.POST)
        if form.is_valid():
            create_asset_group(request.user.id, form.cleaned_data['name'])
            return redirect('/assets/')
        return self.render_to_response(context)

class ManageAssetGroupView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/assets/manage.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['change_name_form'] = CreateAssetGroup()
        context['add_asset_form'] = AddAssetForm(self.request.user.id)
        context['gid'] = self.kwargs['groupid']
        return context
    def post(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        form = CreateAssetGroup(request.POST)
        if form.is_valid():
            groupid = self.kwargs['groupid']
            change_group_name(groupid, form.cleaned_data['name'])
            return redirect("/assets/")
        form = AddAssetForm(request.user.id,request.POST)
        if form.is_valid():
            add_asset_to_group(form.cleaned_data['addresses'], request.user.id, self.kwargs['groupid'])
            return redirect("/assets/")
        return self.render_to_response(context)
        


dashboard_manage_scan_view = ScanManageView.as_view()
dashboard_scan_view = ScanView.as_view()
dashboard_cve_details = CveDetailsView.as_view()
dashboard_main_view = DashboardMainView.as_view()
dashboard_scan_details = ScanDetailsView.as_view()
dashboard_address_view = AddressDashboardView.as_view()
address_details_view = AddressDetailsView.as_view()
address_cve_details_view = AddressCveDetailsView.as_view()
asset_group_view = AssetGroupDashboardView.as_view()
asset_group_create_view = CreateAssetGroupView.as_view()
asset_group_manage_view = ManageAssetGroupView.as_view()