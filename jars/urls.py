import warnings

from django.conf.urls import include, url
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
admin.autodiscover()

from cookies import views, views_rest, views_oaipmh
from cookies.autocomplete import EntityAutocomplete


router = routers.DefaultRouter()
router.register(r'resource', views_rest.ResourceViewSet)
router.register(r'collection', views_rest.CollectionViewSet)
router.register(r'relation', views_rest.RelationViewSet)
router.register(r'field', views_rest.FieldViewSet)
router.register(r'concept', views_rest.ConceptViewSet)
router.register(r'content', views_rest.ContentViewSet)
router.register(r'schema', views_rest.SchemaViewSet)


urlpatterns = [
    url('', include('social_django.urls', namespace='social')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^autocomplete/$', EntityAutocomplete.as_view(create_field='name'), name='autocomplete'),
    url(r'^logout/$', views.logout_view, name='logout'),

    url(r'^resource/([0-9]+)/$', views.resource.resource, name="resource"),
    url(r'^resource/([0-9]+)/content/$', views.resource.resource_content, name="resource-content"),
    url(r'^resource/get/$', views.resource.resource_by_uri, name="resource_by_uri"),
    url(r'^resource/$', views.resource.resource_list, name="resources"),
    url(r'^resource/create/$', views.resource.create_resource, name="create-resource"),
    url(r'^resource/create/upload/$', views.resource.create_resource_file, name="create-resource-file"),
    url(r'^resource/create/remote/$', views.resource.create_resource_url, name="create-resource-url"),
    url(r'^resource/create/giles/$', views.resource.create_resource_choose_giles, name="create-resource-choose-giles"),
    url(r'^resource/create/giles/callback/$', views.giles.handle_giles_upload, name="create-handle-giles"),
    url(r'^resource/merge/$', views.resource.resource_merge, name="resource-merge"),
    url(r'^resource/bulk/$', views.resource.bulk_action_resource, name="bulk-action-resource"),
    url(r'^resource/bulk/addtag/$', views.resource.bulk_add_tag_to_resource, name="bulk-add-tag-to-resource"),
    url(r'^resource/([0-9]+)/edit/$', views.resource.edit_resource_details, name="edit-resource-details"),
    url(r'^resource/([0-9]+)/export/metadata/$', views.resource.export_resource_metadata, name="export-resource-metadata"),
    url(r'^resource/([0-9]+)/giles/([0-9]+)$', views.giles.trigger_giles_submission, name="trigger-giles-submission"),
    url(r'^resource/([0-9]+)/prune/$', views.resource.resource_prune, name="resource-prune"),
    url(r'^resource/([0-9]+)/edit/([0-9]+)/$', views.resource.edit_resource_metadatum, name="edit-resource-metadatum"),
    url(r'^resource/([0-9]+)/edit/([0-9]+)/delete/$', views.resource.delete_resource_metadatum, name="delete-resource-metadatum"),
    url(r'^resource/([0-9]+)/edit/add/$', views.resource.create_resource_metadatum, name='create-resource-metadatum'),
    url(r'^resource/([0-9]+)/contentregions/define/$', views.resource.define_resource_content_region, name='define-resource-content-region'),
    url(r'^resource/create/giles/process/([0-9]+)/$', views.giles.set_giles_upload_collection, name="create-process-giles"),
    url(r'^resource/create/details/([0-9]+)/$', views.resource.create_resource_details, name="create-resource-details"),
    url(r'^resource/create/bulk/$', views.resource.create_resource_bulk, name="create-resource-bulk"),
    url(r'^collection/([0-9]+)/$', views.collection.collection, name="collection"),
    url(r'^collection/([0-9]+)/edit/$', views.collection.collection_edit, name="collection-edit"),
    url(r'^collection/([0-9]+)/authorizations/$', views.collection.collection_authorizations, name="collection-authorizations"),
    url(r'^collection/([0-9]+)/authorizations/create/$', views.collection.collection_authorization_create, name="collection-authorization-create"),
    url(r'^collection/([0-9]+)/authorizations/remove/([0-9]+)/$', views.collection.collection_authorization_remove, name="collection-authorization-remove"),

    url(r'^dataset/create/$', views.resource.create_dataset, name="create-dataset"),
    url(r'^dataset/$', views.resource.list_datasets, name="list-datasets"),
    url(r'^dataset/([0-9]+)/$', views.resource.dataset, name="dataset"),
    url(r'^dataset/([0-9]+)/snapshot/$', views.resource.create_snapshot, name="snapshot-dataset"),

    url(r'^dashboard/$', views.dashboard, name="dashboard"),
    url(r'^inactive/$', views.inactive, name="inactive"),

    url(r'^collection/$', views.collection.collection_list, name="collections"),
    url(r'^collection/create/$', views.collection.create_collection, name="create-collection"),
    url(r'^collection/export/([0-9]+)/$',views.collection.export_coauthor_data, name="export-coauthor-data"),

    url(r'^metadata/$', views.metadata.list_metadata, name='list-metadata'),

    url(r'^entity/$', views.conceptentity.entity_list, name='entity-list'),
    url(r'^entity/merge/$', views.conceptentity.entity_merge, name='entity-merge'),
    url(r'^entity/bulk/$', views.conceptentity.bulk_action_entity, name='bulk-action-entity'),
    url(r'^entity/([0-9]+)/$', views.conceptentity.entity_details, name='entity-details'),
    url(r'^entity/([0-9]+)/change/$', views.conceptentity.entity_change, name='entity-change'),
    url(r'^entity/([0-9]+)/change/concept/$', views.conceptentity.entity_change_concept, name='entity-change-concept'),
    url(r'^entity/([0-9]+)/change/concept/add/$', views.conceptentity.entity_add_concept, name='entity-add-concept'),
    url(r'^entity/([0-9]+)/change/concept/remove/$', views.conceptentity.entity_remove_concept, name='entity-remove-concept'),
    url(r'^entity/([0-9]+)/prune/$', views.conceptentity.entity_prune, name="entity-prune"),
    url(r'^entity/([0-9]+)/relations/([0-9]+)/edit/$', views.conceptentity.entity_edit_relation_as_table, name="entity-edit-relation-as-table"),

    url(r'^giles/log/$', views.giles.log, name="giles-log"),
    url(r'^giles/log/([0-9A-Za-z]+)/$', views.giles.log_item, name="giles-log-item"),
    url(r'^giles/log/([0-9A-Za-z]+)/edit$', views.giles.log_item_edit, name="giles-log-item-edit"),
    url(r'^giles/test/$', views.giles.test_giles, name='giles-test'),
    url(r'^giles/test/configuration/$', views.giles.test_giles_configuration, name='giles-test-configuration'),
    url(r'^giles/test/up/$', views.giles.test_giles_is_up, name='giles-test-is-up'),
    url(r'^giles/test/upload/$', views.giles.test_giles_can_upload, name='giles-test-can-upload'),
    url(r'^giles/test/poll/$', views.giles.test_giles_can_poll, name='giles-test-can-poll'),
    url(r'^giles/test/process/$', views.giles.test_giles_can_process, name='giles-test-can-process'),

    url(r'^giles/test/cleanup/$', views.giles.test_giles_cleanup, name='giles-test-cleanup'),


    url(r'^task/$', views.async.jobs, name='jobs'),
    url(r'^task/([0-9a-z\-]+)/$', views.async.job_status, name='job-status'),

    url(r'^rest/', include(router.urls)),
    url(r'^rest/auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^oaipmh/', views_oaipmh.oaipmh, name='oaipmh'),

    # url(r'^search/$', views.ResourceSearchView.as_view(), name='search'),
    url(r'^s3/', views.resource.sign_s3, name='sign_s3'),
    url(r'^testupload/', views.resource.test_upload, name='test_upload'),
    url(r'^$', views.index, name="index"),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider'))
    ]

urlpatterns += format_suffix_patterns((url(r'^resource_content/([0-9]+)$', views_rest.ResourceContentView.as_view(), name='resource_content'),))
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
