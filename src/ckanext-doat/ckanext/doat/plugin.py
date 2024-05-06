import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.common import _

from six import string_types

import ckanext.doat.cli as cli
import ckanext.doat.helpers as helpers
import ckanext.doat.views as views
from ckanext.doat.logic import (
    action, auth, validators
)
from ckan.lib.plugins import DefaultTranslation
import logging
import os

log = logging.getLogger(__name__)

class DoatPlugin(plugins.SingletonPlugin, DefaultTranslation, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IActions)
    

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        facets_dict['data_type'] = toolkit._('Dataset Type') #ประเภทชุดข้อมูล
        facets_dict['data_category'] = toolkit._('Data Category') #หมวดหมู่ตามธรรมาภิบาลข้อมูล
        facets_dict['data_class_level'] = toolkit._('Data Class Level') #ชั้นความลับของข้อมูลภาครัฐ
        facets_dict['private'] = toolkit._('Visibility') #การเข้าถึง
        return facets_dict

    # IPackageController
    def after_show(self, context, data_dict):
        resources = [resource_dict for resource_dict in data_dict['resources'] if not (resource_dict.get('resource_private','') == "True" and not auth.is_authorized('package_update', context, data_dict).get('success'))]
        data_dict['resources'] = resources
        data_dict['num_resources'] = len(data_dict['resources'])

    def after_search(self, search_results, search_params):
        try:
            if toolkit.c.action == 'action':
                package_list = search_results['results']
                for package_dict in package_list:
                    resources = [resource_dict for resource_dict in package_dict.get('resources',[]) if resource_dict.get('resource_private','') != "True"]
                    package_dict['resources'] = resources
                    package_dict['num_resources'] = len(package_dict['resources'])
        except:
            return search_results
        return search_results

    def _isEnglish(self, s):
        try:
            s.encode(encoding='utf-8').decode('ascii')
        except UnicodeDecodeError:
            return False
        else:
            return True

    def before_search(self, search_params):
        try:
            if 'q' in search_params:
                q = search_params['q']
                lelist = ["+","&&","||","!","(",")","{","}","[","]","^","~","*","?",":","/"]
                contains_word = lambda s, l: any(map(lambda x: x in s, l))
                if len(q) > 0 and len([e for e in lelist if e in q]) == 0:
                    q_list = q.split()
                    q_list_result = []
                    for q_item in q_list:
                        if contains_word(q, ['AND','OR','NOT']) and q_item not in ['AND','OR','NOT'] and not self._isEnglish(q_item):
                            q_item = 'text:*'+q_item+'*'
                        elif contains_word(q, ['AND','OR','NOT']) and q_item not in ['AND','OR','NOT'] and self._isEnglish(q_item):
                            q_item = 'text:'+q_item
                        elif not contains_word(q, ['AND','OR','NOT']) and not self._isEnglish(q_item):
                            q_item = '*'+q_item+'*'
                        q_list_result.append(q_item)
                    q = ' '.join(q_list_result)
                search_params['q'] = q
                if not contains_word(q, ['AND','OR','NOT']):
                    search_params['defType'] = 'edismax'
                    search_params['qf'] = 'name^4 title^4 tags^3 groups^2 organization^2 notes^2 maintainer^2 text'
        except:
            return search_params
        return search_params

    def _unicode_string_convert(self, value):
        values = value.strip('[]').split(',')
        value_list = ""
        for v in values:
            try:
                value_list = value_list + v.strip(' ').encode('latin-1').decode('unicode-escape')
            except:
                value_list = value_list + v
        return "["+value_list.replace('""','","')+"]"

    def _modify_package_before(self, package):
        package.state = 'active'

        for extra in package.extras_list:
            if extra.key == 'objective' and isinstance(extra.value, string_types):
                extra.value = self._unicode_string_convert(extra.value)

    def create(self, package):
        if package.type == 'dataset':
            self._modify_package_before(package)

    def edit(self, package):
        if package.type == 'dataset':
            self._modify_package_before(package)

    # IResourceController
    def before_show(self, res_dict):
        res_dict['created_at'] = res_dict.get('created')
        return res_dict

    # IConfigurer

    def update_config(self, config_):

        if toolkit.check_ckan_version(max_version='2.9'):
            toolkit.add_ckan_admin_tab(config_, 'banner_edit', 'แก้ไขแบนเนอร์')
            toolkit.add_ckan_admin_tab(config_, 'dataset_import', 'นำเข้ารายการชุดข้อมูล')
            toolkit.add_ckan_admin_tab(config_, 'gdc_agency_admin_export', 'ส่งออกรายการชุดข้อมูล')
            toolkit.add_ckan_admin_tab(config_, 'gdc_agency_admin_popup', 'ป็อปอัพ')
        else:
            toolkit.add_ckan_admin_tab(config_, 'banner_edit', u'แก้ไขแบนเนอร์', icon='wrench')
            toolkit.add_ckan_admin_tab(config_, 'dataset_import', u'นำเข้ารายการชุดข้อมูล', icon='cloud-upload')
            toolkit.add_ckan_admin_tab(config_, 'gdc_agency_admin_export', u'ส่งออกรายการชุดข้อมูล', icon='cloud-download')
            toolkit.add_ckan_admin_tab(config_, 'gdc_agency_admin_popup', u'ป็อปอัพ', icon='window-maximize')


        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_public_directory(config_, 'fanstatic')
        toolkit.add_resource("fanstatic", "ckanext-doat")

        try:
            from ckan.lib.webassets_tools import add_public_path
        except ImportError:
            pass
        else:
            asset_path = os.path.join(
                os.path.dirname(__file__), 'fanstatic'
            )
            add_public_path(asset_path, '/')

        config_['ckan.tracking_enabled'] = 'true'
        config_['scheming.dataset_schemas'] = config_.get('scheming.dataset_schemas','ckanext.doat:ckan_dataset.json')
        config_['scheming.presets'] = config_.get('scheming.presets','ckanext.doat:presets.json')
        config_['ckan.activity_streams_enabled'] = 'true'
        config_['ckan.auth.user_delete_groups'] = 'false'
        config_['ckan.auth.user_delete_organizations'] = 'false'
        config_['ckan.auth.public_user_details'] = 'false'
        config_['ckan.datapusher.assume_task_stale_after'] = '60'
        config_['ckan.locale_default'] = 'th'
        config_['ckan.locale_order'] = 'en th pt_BR ja it cs_CZ ca es fr el sv sr sr@latin no sk fi ru de pl nl bg ko_KR hu sa sl lv'
        config_['ckan.datapusher.formats'] = 'csv xls xlsx tsv application/csv application/vnd.ms-excel application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        config_['ckan.group_and_organization_list_all_fields_max'] = '300'
        config_['ckan.group_and_organization_list_max'] = '300'
        config_['ckan.datasets_per_page'] = '30'
        config_['ckan.jobs.timeout'] = '3600'
        config_['ckan.recline.dataproxy_url'] = config_.get('ckan.recline.dataproxy_url','https://dataproxy.gdcatalog.go.th')
        config_['doat.opend_playground_url'] = config_.get('doat.opend_playground_url','https://opend-playground.gdcatalog.go.th')
        config_['doat.gdcatalog_harvester_url'] = config_.get('doat.gdcatalog_harvester_url','https://harvester.gdcatalog.go.th')
        config_['doat.gdcatalog_status_show'] = config_.get('doat.gdcatalog_status_show','true')
        config_['doat.gdcatalog_portal_url'] = config_.get('doat.gdcatalog_portal_url','https://gdcatalog.go.th')
        config_['doat.catalog_org_type'] = config_.get('doat.catalog_org_type','agency') #agency/area_based/data_center
        config_['doat.is_as_a_service'] = config_.get('doat.is_as_a_service', 'false')
        config_['doat.gdcatalog_apiregister_url'] = config_.get('doat.gdcatalog_apiregister_url', 'https://apiregister.gdcatalog.go.th')
        config_['ckan.datastore.sqlsearch.enabled'] = config_.get('ckan.datastore.sqlsearch.enabled', 'false')
        config_['ckan.datastore.search.rows_max'] = config_.get('ckan.datastore.search.rows_max', '10000')
        config_['ckan.upload.admin.mimetypes'] = config_.get('ckan.upload.admin.mimetypes', 'image/png image/gif image/jpeg image/vnd.microsoft.icon application/zip image/x-icon')
        config_['ckan.upload.admin.types'] = config_.get('ckan.upload.admin.types', 'image application')

    
    # IAuthFunctions

    def get_auth_functions(self):
        return auth.get_auth_functions()

    # IActions

    def get_actions(self):
        return action.get_actions()

    # IBlueprint

    def get_blueprint(self):
        return views.get_blueprints()

    # IClick

    # def get_commands(self):
    #     return cli.get_commands()

    # ITemplateHelpers

    def get_helpers(self):
        return helpers.get_helpers()

    # IValidators

    def get_validators(self):
        return validators.get_validators()
    
