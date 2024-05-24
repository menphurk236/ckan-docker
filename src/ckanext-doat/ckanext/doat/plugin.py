#!/usr/bin/env python
# encoding: utf-8

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.common import _
from ckan.lib.plugins import DefaultTranslation
import ckan.model as model

from six import string_types

from actions import exporter_action, popup_action, opend_action
from ckanext.doat import auth as doat_auth
from ckanext.doat import helpers as doat_h
from ckanext.doat import validation as doat_validator

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
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IActions)

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        facets_dict['data_type'] = toolkit._('DatasetType') #ประเภทชุดข้อมูล
        facets_dict['data_category'] = toolkit._('DataCategory') #หมวดหมู่ตามธรรมาภิบาลข้อมูล
        facets_dict['data_class_level'] = toolkit._('DataClassLevel') #ชั้นความลับของข้อมูลภาครัฐ
        facets_dict['private'] = toolkit._('Visibility') #การเข้าถึง
        return facets_dict

    # IPackageController

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

    def before_view(self, pkg_dict):
        pkg_dict['tracking_summary'] = (model.TrackingSummary.get_for_package(pkg_dict['id']))
        return pkg_dict

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

        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_public_directory(config_, 'fanstatic')
        toolkit.add_resource('fanstatic', 'doat')

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
        config_['scheming.dataset_schemas'] = config_.get('scheming.dataset_schemas','ckanext.thai_gdc:ckan_dataset.json')
        config_['scheming.presets'] = config_.get('scheming.presets','ckanext.thai_gdc:presets.json')
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
        config_['thai_gdc.opend_playground_url'] = config_.get('thai_gdc.opend_playground_url','https://opend-playground.gdcatalog.go.th')
        config_['thai_gdc.gdcatalog_harvester_url'] = config_.get('thai_gdc.gdcatalog_harvester_url','https://harvester.gdcatalog.go.th')
        config_['thai_gdc.gdcatalog_status_show'] = config_.get('thai_gdc.gdcatalog_status_show','true')
        config_['thai_gdc.gdcatalog_portal_url'] = config_.get('thai_gdc.gdcatalog_portal_url','https://gdcatalog.go.th')
        config_['thai_gdc.catalog_org_type'] = config_.get('thai_gdc.catalog_org_type','agency') #agency/area_based/data_center
        config_['thai_gdc.is_as_a_service'] = config_.get('thai_gdc.is_as_a_service', 'false')
        config_['thai_gdc.gdcatalog_apiregister_url'] = config_.get('thai_gdc.gdcatalog_apiregister_url', 'https://apiregister.gdcatalog.go.th')
        config_['ckan.datastore.sqlsearch.enabled'] = config_.get('ckan.datastore.sqlsearch.enabled', 'false')
        config_['ckan.datastore.search.rows_max'] = config_.get('ckan.datastore.search.rows_max', '10000')
        config_['ckan.upload.admin.mimetypes'] = config_.get('ckan.upload.admin.mimetypes', 'image/png image/gif image/jpeg image/vnd.microsoft.icon application/zip image/x-icon')
        config_['ckan.upload.admin.types'] = config_.get('ckan.upload.admin.types', 'image application')


    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')
        unicode_safe = toolkit.get_validator('unicode_safe')
        schema.update({
            'ckan.site_org_address': [ignore_missing, unicode_safe],
            'ckan.site_org_contact': [ignore_missing, unicode_safe],
            'ckan.site_org_email': [ignore_missing, unicode_safe],
            'ckan.site_policy_link': [ignore_missing, unicode_safe],
            'ckan.promoted_banner': [ignore_missing, unicode_safe],
            'promoted_banner_upload': [ignore_missing, unicode_safe],
            'clear_promoted_banner_upload': [ignore_missing, unicode_safe],
            'ckan.search_background': [ignore_missing, unicode_safe],
            'search_background_upload': [ignore_missing, unicode_safe],
            'clear_search_background_upload': [ignore_missing, unicode_safe],
            'template_file': [ignore_missing, unicode_safe],
            'template_file_upload': [ignore_missing, unicode_safe],
            'clear_template_file_upload': [ignore_missing, unicode_safe],
            'import_org': [ignore_missing, unicode_safe],
            'import_log': [ignore_missing, unicode_safe],
            'template_org': [ignore_missing, unicode_safe],
            'ckan.favicon': [ignore_missing, unicode_safe],
            'favicon_upload': [ignore_missing, unicode_safe],
            'clear_favicon_upload': [ignore_missing, unicode_safe],
            'ckan.import_uuid': [ignore_missing, unicode_safe],
            'ckan.import_row': [ignore_missing, unicode_safe],
            'ckan.import_params': [ignore_missing, unicode_safe],
        })
        return schema
    
    # IRoutes
    def before_map(self, map):
        map.connect(
            'banner_edit',
            '/ckan-admin/banner-edit',
            action='edit_banner',
            ckan_icon='wrench',
            controller='ckanext.doat.controllers.banner:BannerEditController',
        )
        map.connect(
            'dataset_import',
            '/ckan-admin/dataset-import',
            action='import_dataset',
            ckan_icon='cloud-upload',
            controller='ckanext.doat.controllers.dataset:DatasetImportController',
        )
        map.connect(
            'clear_import_log',
            '/ckan-admin/clear-import-log',
            action='clear_import_log',
            controller='ckanext.doat.controllers.dataset:DatasetImportController',
        )
        map.connect(
            'dataset_datatype_patch',
            '/dataset/edit-datatype/{package_id}',
            action='datatype_patch',
            controller='ckanext.doat.controllers.dataset:DatasetManageController',
        )
        map.connect(
            'user_active',
            '/user/edit/user_active',
            action='user_active',
            controller='ckanext.doat.controllers.user:UserManageController',
        )
        # map.connect(
        #     'organizations_index',
        #     '/organization/',
        #     action='index',
        #     controller='ckanext.doat.controllers.organization:OrganizationCustomController'
        # )
        # map.connect(
        #     'organizations_index',
        #     '/organization',
        #     action='index',
        #     controller='ckanext.doat.controllers.organization:OrganizationCustomController'
        # )
        map.connect(
            'gdc_agency_admin_export',
            '/ckan-admin/dataset-export',
            action='index',
            ckan_icon='file',
            controller='ckanext.doat.controllers.export_package:ExportPackageController'
        )
        map.connect(
            'gdc_agency_admin_download',
            '/ckan-admin/dataset-export/{id:.*|}',
            action='download',
            ckan_icon='file',
            controller='ckanext.doat.controllers.export_package:ExportPackageController'
        )
        map.connect(
            'gdc_agency_admin_popup',
            '/ckan-admin/dataset-popup',
            action='index',
            ckan_icon='file',
            controller='ckanext.doat.controllers.popup:PopupController'
        )
        return map
    
    
    # IAuthFunctions
    def get_auth_functions(self):
        auth_functions = {
            'member_create': doat_auth.member_create,
            'user_generate_apikey': doat_auth.user_generate_apikey,
            'resource_show': doat_auth.restrict_resource_show,
            'resource_view_show': doat_auth.restrict_resource_show,
            'package_delete': doat_auth.package_delete,
            'resource_delete': doat_auth.resource_delete,
            'resource_view_reorder': doat_auth.resource_view_reorder,
        }
        return auth_functions

# IActionFunctions
    def get_actions(self):
        action_functions = {
            'bulk_update_public': opend_action.bulk_update_public,
            'dataset_bulk_import': opend_action.dataset_bulk_import,
            'tag_list': opend_action.tag_list,
            'group_type_patch': opend_action.group_type_patch,
            'status_show': opend_action.status_show,
            'gdc_agency_export_package': exporter_action.package,
            'gdc_agency_get_conf_group': popup_action.get_conf_group,
            'gdc_agency_update_conf_group': popup_action.update_conf_group,
            'resource_view_create': opend_action.resource_view_create,
            'resource_view_update': opend_action.resource_view_update,
            'resource_view_delete': opend_action.resource_view_delete,
            'resource_view_reorder' : opend_action.resource_view_reorder,
        }
        return action_functions

    # IValidators
    def get_validators(self):
        return {
            'tag_name_validator': doat_validator.tag_name_validator,
            'tag_string_convert': doat_validator.tag_string_convert,
            'package_name_validator': doat_validator.package_name_validator,
            'package_title_validator': doat_validator.package_title_validator,
        }

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'doat_get_organizations': doat_h.get_organizations,
            'doat_get_groups': doat_h.get_groups,
            'doat_get_resource_download': doat_h.get_resource_download,
            'doat_day_thai': doat_h.day_thai,
            'doat_get_stat_all_view': doat_h.get_stat_all_view,
            'doat_get_last_update_tracking': doat_h.get_last_update_tracking,
            'doat_facet_chart': doat_h.facet_chart,
            'doat_get_page': doat_h.get_page,
            'doat_get_recent_view_for_package': doat_h.get_recent_view_for_package,
            'doat_get_featured_pages': doat_h.get_featured_pages,
            'doat_get_all_groups': doat_h.get_all_groups,
            'doat_get_all_groups_all_type': doat_h.get_all_groups_all_type,
            'doat_get_action': doat_h.get_action,
            'doat_get_extension_version': doat_h.get_extension_version,
            'doat_get_users_deleted': doat_h.get_users_deleted,
            'doat_get_users_non_member': doat_h.get_users_non_member,
            'doat_get_gdcatalog_state': doat_h.get_gdcatalog_state,
            'doat_get_opend_playground_url': doat_h.get_opend_playground_url,
            'doat_get_catalog_org_type': doat_h.get_catalog_org_type,
            'doat_get_gdcatalog_status_show': doat_h.get_gdcatalog_status_show,
            'doat_get_gdcatalog_portal_url': doat_h.get_gdcatalog_portal_url,
            'doat_get_gdcatalog_apiregister_url': doat_h.get_gdcatalog_apiregister_url,
            'doat_convert_string_todate': doat_h.convert_string_todate,
            'doat_get_group_color': doat_h.get_group_color,
            'doat_dataset_bulk_import_status': doat_h.dataset_bulk_import_status,
            'doat_dataset_bulk_import_count': doat_h.dataset_bulk_import_count,
            'doat_dataset_bulk_import_log': doat_h.dataset_bulk_import_log,
            'doat_get_is_as_a_service': doat_h.get_is_as_a_service,
            'doat_get_gdcatalog_version_update': doat_h.get_gdcatalog_version_update,
            'doat_users_in_organization': doat_h.users_in_organization,
            'doat_get_user_display_name': doat_h.get_user_display_name,
            'gdc_agency_get_suggest_view': doat_h.get_suggest_view,
            'gdc_agency_get_conf_group': doat_h.get_conf_group,
            'nso_get_last_modified_datasets': doat_h.get_last_modified_datasets,
            'nso_get_popular_datasets' : doat_h.get_popular_datasets,
            'get_site_statistics': doat_h.get_site_statistics
        }