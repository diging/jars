from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.conf import settings

from cookies.models import *
from cookies.filters import *
from cookies.forms import *
from cookies import authorization as auth

from itertools import groupby

from . import resource, collection, async, conceptentity, metadata, giles


def index(request):
    return render(request, 'index.html', {})


@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(request.GET.get('next', reverse('index')))


@login_required
def dashboard(request):
    qs = GilesUpload.objects.filter(created_by=request.user)
    resources = auth.apply_filter(ResourceAuthorization.VIEW, request.user,
                                  ResourceContainer.active.all())
    filtered_resources = ResourceContainerFilter({'created_by': request.user.id}, queryset=resources)

    context = {
        'uploads_pending': qs.filter(state=GilesUpload.PENDING).count(),
        'uploads_enqueued': qs.filter(state=GilesUpload.ENQUEUED).count(),
        'uploads_send_error': qs.filter(state=GilesUpload.SEND_ERROR).count(),
        'uploads_giles_error': qs.filter(state=GilesUpload.GILES_ERROR).count(),
        'uploads_sent': qs.filter(state=GilesUpload.SENT).count(),
        'uploads_process_error': qs.filter(state=GilesUpload.PROCESS_ERROR).count(),
        'uploads_callback_error': qs.filter(state=GilesUpload.CALLBACK_ERROR).count(),
        'uploads_done': qs.filter(state=GilesUpload.DONE).count(),
        'uploads_assigned': qs.filter(state=GilesUpload.ASSIGNED).count(),
        'resources': filtered_resources.qs.order_by('-created')[:5],
        'PENDING': GilesUpload.PENDING,
        'ENQUEUED': GilesUpload.ENQUEUED,
        'SENT': GilesUpload.SENT,
        'DONE': GilesUpload.DONE,
        'SEND_ERROR': GilesUpload.SEND_ERROR,
        'PROCESS_ERROR': GilesUpload.PROCESS_ERROR,
        'GILES_ERROR': GilesUpload.GILES_ERROR,
        'CALLBACK_ERROR': GilesUpload.CALLBACK_ERROR,
        'ASSIGNED': GilesUpload.ASSIGNED,
        'all_uploads_pending': GilesUpload.objects.filter(state=GilesUpload.PENDING).count(),
        'all_uploads_enqueued': GilesUpload.objects.filter(state=GilesUpload.ENQUEUED).count(),
        'all_uploads_send_error': GilesUpload.objects.filter(state=GilesUpload.SEND_ERROR).count(),
        'all_uploads_giles_error': GilesUpload.objects.filter(state=GilesUpload.GILES_ERROR).count(),
        'all_uploads_sent': GilesUpload.objects.filter(state=GilesUpload.SENT).count(),
        'all_uploads_process_error': GilesUpload.objects.filter(state=GilesUpload.PROCESS_ERROR).count(),
        'all_uploads_callback_error': GilesUpload.objects.filter(state=GilesUpload.CALLBACK_ERROR).count(),
        'all_uploads_done': GilesUpload.objects.filter(state=GilesUpload.DONE).count(),
        'all_uploads_assigned': GilesUpload.objects.filter(state=GilesUpload.ASSIGNED).count(),
    }
    return render(request, 'dashboard.html', context)


def inactive(request):
    return render(request, 'inactive.html', {'admin_email': settings.ADMIN_EMAIL})
