from __future__ import absolute_import

from django.conf import settings

from celery import shared_task, task

from cookies import content, giles, authorization, operations
from cookies.models import *
from concepts import authorities
from cookies.accession import IngesterFactory
from cookies.exceptions import *
from django.core.files import File
logger = settings.LOGGER

import jsonpickle, json, datetime


@shared_task
def handle_content(obj, commit=True):
    """
    Attempt to extract plain text from content files associated with a
    :class:`.Resource` instance.

    Parameters
    ----------
    obj : :class:`.Resource`
    commit : bool
    """
    return content.handle_content(obj, commit)


@task(name='jars.tasks.handle_bulk', bind=True)
def handle_bulk(self, file_path, form_data, file_name, job=None,
                ingester='cookies.accession.zotero.ZoteroIngest'):
    """
    Process resource data in a RDF document.

    Parameters
    ----------
    file_path : str
        Local path to a RDF document, or a ZIP file containing a Zotero RDF
        export (with files).
    form_data : dict
        Valid data from a :class:`cookies.forms.BulkResourceForm`\.
    file_name : str
        Name of the target file at ``file_path``\.
    job : :class:`.UserJob`
        Used to update progress.
    """
    if job:
        job.result_id = self.request.id
        job.save()

    logger.debug('handle bulk')
    creator = form_data.pop('created_by')

    # The user can either add these new records to an existing collection, or
    #  create a new one.
    collection = form_data.pop('collection', None)
    collection_name = form_data.pop('name', None)
    if not collection:
        collection = Collection.objects.create(**{
            'name': collection_name,
            'created_by': creator,
        })

    operations.add_creation_metadata(collection, creator)

    # User can indicate a default Type to assign to each new Resource.
    default_type = form_data.pop('default_type', None)
    upload_resource = Resource.objects.create(
        created_by=creator,
        name=file_name,
    )
    with open(file_path, 'r') as f:
        upload_resource.file.save(file_name, File(f), True)

    ingester = IngesterFactory().get(ingester)(upload_resource.file.path)
    ingester.Resource = authorization.apply_filter(ResourceAuthorization.EDIT, creator, ingester.Resource)
    ingester.Collection = authorization.apply_filter(ResourceAuthorization.EDIT, creator, ingester.Collection)
    ingester.ConceptEntity = authorization.apply_filter(ResourceAuthorization.EDIT, creator, ingester.ConceptEntity)
    ingester.set_resource_defaults(entity_type=default_type,
                                   collection=collection,
                                   created_by=creator, **form_data)

    N = len(ingester)
    for resource in ingester:
        resource.container.part_of = collection
        resource.container.save()
        # collection.resources.add(resource)
        operations.add_creation_metadata(resource, creator)

        if job:
            job.progress += 1./N
            job.save()
    job.result = jsonpickle.encode({'view': 'collection', 'id': collection.id})
    job.save()

    return {'view': 'collection', 'id': collection.id}


@shared_task
def send_to_giles(upload_pk, created_by):
    print '::: sending Giles upload %s :::' % upload_pk
    giles.send_giles_upload(upload_pk, created_by)


@shared_task
def check_giles_upload(upload_id, username):
    print '::async:: check_giles_upload', upload_id, username
    return giles.process_upload(upload_id, username)


@shared_task
def search_for_concept(lemma):
    authorities.searchall(lemma)


@shared_task
def check_giles_uploads():
    """
    Periodic task that reviews currently outstanding Giles uploads, and checks
    their status.
    """
    from datetime import datetime, timedelta

    for upload in GilesUpload.objects.filter(state=GilesUpload.PENDING):
        print '::: adding %s to Giles upload queue :::' % upload.id
        send_to_giles.delay(upload.id, upload.created_by)
        upload.state = GilesUpload.ENQUEUED
        upload.save()

    for upload_id, username in GilesUpload.objects.filter(state=GilesUpload.SENT).filter(Q(last_checked__gte=datetime.now() - timedelta(seconds=120)) | Q(last_checked=None)).values_list('upload_id', 'created_by__username'):
        print '::: checking upload status for %s :::' % upload_id
        check_giles_upload.delay(upload_id, username)



# @shared_task
# def send_giles_uploads():
#     """
#     Check for outstanding :class:`.GilesUpload`\s, and send as able.
#     """
#     logger.debug('Checking for outstanding GilesUploads')
#     query = Q(resolved=False) & ~Q(sent=None) & Q(fail=False)
#     outstanding = GilesUpload.objects.filter(query)
#     pending = GilesUpload.objects.filter(resolved=False, sent=None, fail=False)
#
#     # We limit the number of simultaneous requests to Giles.
#     remaining = settings.MAX_GILES_UPLOADS - outstanding.count()
#     if remaining <= 0 or pending.count() == 0:
#         return
#
#     logger.debug('Found GilesUpload, processing...')
#
#     to_upload = min(remaining, pending.count())
#     if to_upload <= 0:
#         return
#
#     for upload in pending[:to_upload]:
#         content_resource = upload.content_resource
#         creator = content_resource.created_by
#         resource = content_resource.parent.first().for_resource
#
#         anonymous, _ = User.objects.get_or_create(username='AnonymousUser')
#         public = authorization.check_authorization('view', anonymous,
#                                                    content_resource)
#         result = send_to_giles(content_resource.file.name, creator,
#                                resource=resource, public=public,
#                                gilesupload_id=upload.id)
