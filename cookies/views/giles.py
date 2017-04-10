from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.conf import settings

from cookies import operations
from cookies import authorization as auth
from cookies.models import *
from cookies.forms import ChooseCollectionForm
from cookies import giles


@login_required
def handle_giles_upload(request):
    """
    If the user uploaded a file directly through Giles, they may be redirected
    to Amphora to enter metadata. In that case, we don't yet know about this
    upload, and will need to create new resources from scratch.
    """
    upload_ids = request.GET.getlist('uploadids') + request.GET.getlist('uploadIds')
    if not upload_ids:
        raise RuntimeError('Seriously??')   # TODO: something more informative.

    for uid in upload_ids:
        tasks.check_giles_upload.delay(upload_id, request.user.username)

    _tail = '&'.join(['upload_id=%s' % uid for uid in upload_ids])
    return HttpResponseRedirect(reverse('giles-upload-status') + _tail)


@login_required
def giles_upload_status(request):
    """
    Display the current state of one or several :class:`.GilesUpload`\s.
    """
    upload_ids = request.GET.getlist('upload_id')
    context = {
        'uploads': [GilesUpload.objects.get(pk=uid) for uid in upload_ids]
    }
    return render(request, 'giles_upload_status.html', context)


@login_required
def set_giles_upload_collection(request, upload_id):
    """
    User can add a resource created from a :class:`.GilesUpload` to a
    :class:`.Collection`\.
    """
    upload = get_object_or_404(GilesUpload, upload_id=upload_id)
    if not upload.state == GilesUpload.DONE:
        raise RuntimeError('Not ready')
    if not upload.resource:
        raise RuntimeError('No resource')
    if upload.created_by != request.user:
        raise RuntimeError('WTF')    # TODO: say something more informative.

    context = {'upload': upload,}

    if request.method == 'GET':
        form = ChooseCollectionForm()

        # User can only add resources to collections for which they have ADD
        #  privileges.
        qs = auth.apply_filter(CollectionAuthorization.ADD, request.user,
                               form.fields['collection'].queryset)
        form.fields['collection'].queryset = qs

    elif request.method == 'POST':
        form = ChooseCollectionForm(request.POST)

        # User can only add resources to collections for which they have ADD
        #  privileges.
        qs = auth.apply_filter(CollectionAuthorization.ADD, request.user,
                               form.fields['collection'].queryset)
        form.fields['collection'].queryset = qs

        if form.is_valid():
            collection = form.cleaned_data.get('collection', None)
            name = form.cleaned_data.get('name', None)

            # The user has the option to create a new Collection by leaving the
            #  collection field blank and providing a name.
            if collection is None and name is not None:
                collection = Collection.objects.create(**{
                    'created_by_id': request.user.id,
                    'name': name,
                })
                operations.add_creation_metadata(collection, request.user)
            form.fields['collection'].initial = collection.id
            form.fields['name'].widget.attrs['disabled'] = True

            upload.resource.container.part_of = collection
            upload.resource.container.save()

    context.update({'form': form})
    return render(request, 'create_process_giles_upload.html', context)


@auth.authorization_required(ResourceAuthorization.EDIT, lambda resource_id: get_object_or_404(Resource, pk=resource_id))
def trigger_giles_submission(request, resource_id, relation_id):
    """
    Manually start the Giles upload process.
    """
    resource = _get_resource_by_id(request, resource_id)
    instance = resource.content.get(pk=relation_id)
    import mimetypes
    content_type = instance.content_resource.content_type or mimetypes.guess_type(instance.content_resource.file.name)[0]
    if instance.content_resource.is_local and instance.content_resource.file.name is not None:
        # All files should be sent.
        upload_pk = giles.create_giles_upload(resource.id, instance.id,
                                              request.user.username,
                                              settings.DELETE_LOCAL_FILES)


@staff_member_required
def test_giles(request):
    return render(request, 'test_giles.html', {})


@staff_member_required
def test_giles_configuration(request):
    return JsonResponse({'giles_endpoint': settings.GILES, 'giles_token': settings.GILES_APP_TOKEN[:10] + '...'})


@staff_member_required
def test_giles_is_up(request):
    import requests
    giles = settings.GILES
    response = requests.head(giles)
    context = {
        'response_code': response.status_code,
    }
    return JsonResponse(context)


@staff_member_required
def test_giles_can_upload(request):
    """
    Send a test file to Giles.
    """
    from django.core.files import File
    import os


    user = request.user
    resource = Resource.objects.create(name='test resource', created_by=user)
    container = ResourceContainer.objects.create(primary=resource, created_by=user)
    resource.container = container
    resource.save()
    file_path = os.path.join(settings.MEDIA_ROOT, 'test.ack')
    with open(file_path, 'w') as f:
        test_file = File(f)
        test_file.write('this is a test file')

    with open(file_path, 'r') as f:
        test_file = File(f)
        content_resource = Resource.objects.create(content_resource=True, file=test_file, created_by=user, container=container)
    content_relation = ContentRelation.objects.create(for_resource=resource, content_resource=content_resource, created_by=user, container=container)

    upload_pk = giles.create_giles_upload(resource.id, content_relation.id,
                                       user.username,
                                       delete_on_complete=True)
    giles.send_giles_upload(upload_pk, user.username)
    upload = GilesUpload.objects.get(pk=upload_pk)

    context = {
        'status': upload.state,
        'upload_id': upload.upload_id,
        'container_id': container.id,
    }
    return JsonResponse(context)


@staff_member_required
def test_giles_can_poll(request):
    upload_id = request.GET.get('upload_id')
    try:
        giles.check_upload_status(request.user.username, upload_id)
    except giles.StatusException:
        return JsonResponse({'status': 'FAILED'})
    upload = GilesUpload.objects.get(upload_id=upload_id)
    context = {
        'status': upload.state,
    }
    return JsonResponse(context)


@staff_member_required
def test_giles_can_process(request):
    upload_id = request.GET.get('upload_id')
    giles.process_upload(upload_id, request.user.username)
    upload = GilesUpload.objects.get(upload_id=upload_id)
    context = {
        'status': upload.state,
    }
    return JsonResponse(context)


@staff_member_required
def test_giles_cleanup(request):
    upload_id = request.GET.get('upload_id')
    container_id = request.GET.get('container_id')
    container = ResourceContainer.objects.get(pk=container_id)
    container.relation_set.all().delete()
    container.resource_set.all().delete()
    container.delete()

    try:
        GilesUpload.objects.get(upload_id=upload_id).delete()
    except GilesUpload.DoesNotExist:
        pass
    return JsonResponse({'status': 'ok'})