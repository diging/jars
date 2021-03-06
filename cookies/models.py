from django.db import models, IntegrityError, transaction
from django.db.models.query import Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.conf import settings
from pg_fts.fields import TSVectorField


import iso8601, json, sys, six, logging, rest_framework, jsonpickle, os
from uuid import uuid4

logger = settings.LOGGER

from django.conf import settings
import concepts


def _resource_file_name(instance, filename):
    """
    Generates a file name for Files added to a :class:`.LocalResource`\.

    E.g. if the content resource has ID 12345 and ``filename == 'file.txt'``,
    the path (relative to MEDIA_ROOT) will be ``1/2/3/4/5/content/file.txt``.

    Parameters
    ----------
    instance : :class:`.Resource`
    filename : str
        File name or path to file (only the head will be used).
    """
    full_ident = list(unicode(instance.id))
    return u'/'.join(full_ident + ['content', os.path.split(filename)[-1]])


# TODO: include filtering of hidden records?
class ActiveManager(models.Manager):
    """
    Convenience manager for filtering out "deleted" records. This can be used
    with any model that inherits from :class:`.Entity`\.
    """
    def get_queryset(self):
        return super(ActiveManager, self).get_queryset().filter(is_deleted=False)


class Entity(models.Model):
    """
    A named object that represents some element in the data.
    """

    INTERFACE_WEB = 'WEB'
    INTERFACE_API = 'API'
    INTERFACES = (
        (INTERFACE_WEB, 'Web UI'),
        (INTERFACE_API, 'API'),
    )

    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, blank=True, null=True)
    created_through = models.CharField(null=True, max_length=3, choices=INTERFACES)
    updated = models.DateTimeField(auto_now=True)

    entity_type = models.ForeignKey('Type', blank=True, null=True,
                                    verbose_name='type', help_text="Specifying"
    " a type helps to determine what metadata fields are appropriate for this"
    " resource, and can help with searching. Note that type-specific filtering"
    " of metadata fields will only take place after this resource has been"
    " saved.")

    name = models.CharField(max_length=2000)

    hidden = models.BooleanField(default=False)
    """
    If a resource is hidden it will not appear in search results and will
    not be accessible directly, even for logged-in users.
    """

    # TODO: remove this field; it is no longer relevant.
    public = models.BooleanField(default=False, help_text="If a resource is not"
    " public it will only be accessible to logged-in users and will not appear"
    " in public search results. If this option is selected, you affirm that you"
    " have the right to upload and distribute this resource.")

    namespace = models.CharField(max_length=255, blank=True, null=True)
    uri = models.CharField(db_index=True, max_length=255, verbose_name='URI', help_text="You"
    " may provide your own URI, or allow the system to assign one"
    " automatically.")

    relations_from = GenericRelation('Relation',
                                     content_type_field='source_type',
                                     object_id_field='source_instance_id')

    relations_to = GenericRelation('Relation',
                                   content_type_field='target_type',
                                   object_id_field='target_instance_id')

    is_deleted = models.BooleanField(default=False)

    container = models.ForeignKey('ResourceContainer', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'entities'
        abstract = True

    def save(self, *args, **kwargs):
        super(Entity, self).save(*args, **kwargs)
        # Generate a URI if one has not already been assigned.
        #  TODO: this should call a method to generate a URI, to allow for more
        #        flexibility (e.g. calling a Handle server).
        if not self.uri:
            ns = settings.URI_NAMESPACE
            if ns.endswith('/'):
                ns = ns[:-1]
            self.uri = '/'.join([ns, self.__class__.__name__.lower(), str(self.id)])
        super(Entity, self).save()

    def __unicode__(self):
        return unicode(self.id)


class ResourceBase(Entity):
    """
    Provides some generic fields for :class:`.Resource` and :class:`.Collection`
    models.
    """

    # TODO: remove indexable_content and processed, as they are no longer used.
    indexable_content = models.TextField(blank=True, null=True)
    processed = models.BooleanField(default=False)

    content_type = models.CharField(max_length=255, blank=True, null=True)

    # If true, we expect (by convention) that either ``file`` or ``location``
    #  will be set.
    content_resource = models.BooleanField(default=False)

    file = models.FileField(upload_to=_resource_file_name, blank=True,
                            null=True, max_length=2000)

    location = models.TextField(db_column='location', verbose_name='URL', blank=True, null=True)

    # TODO: remove this property.
    @property
    def text_available(self):
        if self.indexable_content:
            return len(self.indexable_content) > 2
        return False

    def get_absolute_url(self):
        return reverse("resource", args=(self.id,))

    @property
    def is_local(self):
        if self.file:
            return True
        elif self.location:
            return False

    @property
    def parts(self):
        """
        Many resources will have several parts (e.g. pages), which are connected
        via :class:`.Relation` entries.
        """
        __isPartOf__, _ = Field.objects.get_or_create(uri=settings.IS_PART_OF)
        return self.relations_to.filter(predicate=__isPartOf__).order_by('sort_order')

    class Meta:
        abstract = True


class Resource(ResourceBase):
    objects = models.Manager()
    active = ActiveManager()

    next_page = models.OneToOneField('Resource', related_name='previous_page',
                                     blank=True, null=True)

    is_part = models.BooleanField(default=False)
    is_external = models.BooleanField(default=False)

    GILES = 'GL'
    WEB = 'WB'
    HATHITRUST = 'HT'
    SOURCES = (
        (GILES, 'Giles'),
        (WEB, 'Web'),
        (HATHITRUST, 'HathiTrust'),
    )
    external_source = models.CharField(max_length=2, choices=SOURCES,
                                       blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    name_index = TSVectorField(('name',), dictionary='simple')
    location_id = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Instead of storing the complete resource URL in `location`, "
                  "use this field to store the unique part of URL and generate "
                  "the complete URL at runtime.""",
    )

    def __getattribute__(self, attr):
        if attr != 'location':
            return super(Resource, self).__getattribute__(attr)
        location = super(Resource, self).__getattribute__(attr)
        if location:
            return location
        if self.location_id and self.external_source == self.GILES:
            return settings.GILES_CONTENT_FORMAT_STRING.format(giles_file_id=self.location_id)
        return None

    @property
    def active_content(self):
        return self.content.filter(is_deleted=False, hidden=False)

    @property
    def content_location(self):
        if self.content_resource:
            if self.file:
                return self.file.url
            return reverse('resource-content', args=(self.id,))

    @property
    def content_types(self):
        return list(self.container.content_relations.values_list('content_type', flat=True).distinct('content_type'))

    @property
    def content_view(self):
        return reverse('resource-content', args=(self.id,))

    @property
    def is_remote(self):
        return not self.is_local and not self.is_external

    @property
    def has_giles_content(self):
        return self.content.filter(content_resource__external_source=Resource.GILES).count() > 0

    @property
    def has_local_content(self):
        return self.content.filter(~Q(content_resource__file='')).count() > 0

    OK = 'OK'
    PROCESSING = 'PR'
    ERROR = 'ER'
    @property
    def state(self):
        if self.giles_uploads.count() == 0:
            return Resource.OK
        states = self.giles_uploads.values_list('state', flat=True)
        if any(map(lambda s: s in GilesUpload.ERROR_STATES, states)):
            return Resource.ERROR
        if all(map(lambda s: s == GilesUpload.DONE, states)):
            return Resource.OK
        return Resource.PROCESSING

    relations_from_resource = GenericRelation('Relation',
                                     content_type_field='source_type',
                                     object_id_field='source_instance_id',
                                     related_query_name='source_resource')

    relations_to_resource = GenericRelation('Relation',
                                   content_type_field='target_type',
                                   object_id_field='target_instance_id',
                                   related_query_name='target_resource')


class ContentRegion(Entity):
    objects = models.Manager()
    active = ActiveManager()
    start_position = models.IntegerField()
    start_resource = models.ForeignKey('Resource', related_name='resource_start',
                                       on_delete=models.CASCADE)
    end_position = models.IntegerField()
    end_resource = models.ForeignKey('Resource', related_name='resource_end',
                                     on_delete=models.CASCADE)


class Tag(models.Model):
    """
    """
    created_by = models.ForeignKey(User, related_name='tags')
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)


class ResourceTag(models.Model):
    """
    """
    created_by = models.ForeignKey(User, related_name='resource_tags')
    created = models.DateTimeField(auto_now_add=True)
    tag = models.ForeignKey('Tag', related_name='resource_tags')
    resource = models.ForeignKey('Resource', related_name='tags')


class ContentRelation(models.Model):
    """
    Associates a :class:`.Resource` with its content representation(s).
    """

    objects = models.Manager()
    active = ActiveManager()

    for_resource = models.ForeignKey('Resource', related_name='content')
    content_resource = models.ForeignKey('Resource', related_name='parent')
    content_type = models.CharField(max_length=100, null=True, blank=True)
    content_encoding = models.CharField(max_length=100, null=True, blank=True)

    created_by = models.ForeignKey(User, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    container = models.ForeignKey('ResourceContainer',
                                  related_name='content_relations')
    is_deleted = models.BooleanField(default=False)

class Collection(ResourceBase):
    """
    A set of :class:`.Entity` instances.
    """
    objects = models.Manager()
    active = ActiveManager()

    part_of = models.ForeignKey('Collection', blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    def get_number_of_conceptentities(self):
        """
        Count all of the :class:`.ConceptEntity` instances associated with
        resources in this :class:`.Collection`\.
        """
        return len(set(self.resourcecontainer_set.values_list('conceptentity__id')))

    def get_absolute_url(self):
        return reverse("collection", args=(self.id,))

    def __unicode__(self):
        return self.name

    @property
    def subcollections(self):
        return self.collection_set.all()

    @property
    def children(self):
        children_ids = []
        def _decomp(obj):
            for item in obj:
                if isinstance(item, list):
                    _decomp(item)
                else:
                    children_ids.append(item)
        def _get_children(collection_id):
            return [collection_id] + map(_get_children, filter(lambda pk: pk is not None, Collection.objects.filter(part_of_id=collection_id).values_list('id', flat=True)))
        _decomp(_get_children(self))
        return children_ids

    @property
    def size(self):
        return ResourceContainer.objects.filter(part_of_id__in=self.children).count()

    @property
    def resources(self):
        return Resource.objects.filter(is_primary_for__part_of_id=self.id,
                                       is_deleted=False)


### Types and Fields ###


class Schema(models.Model):
    name = models.CharField(max_length=255)

    namespace = models.CharField(max_length=255, blank=True, null=True)
    uri = models.CharField(max_length=255, blank=True, null=True,
                           verbose_name='URI')

    active = models.BooleanField(default=True)
    prefix = models.CharField(max_length=10, blank=True, null=True)

    def __unicode__(self):
        return unicode(self.name)


class Type(models.Model):
    name = models.CharField(max_length=255)

    namespace = models.CharField(max_length=255, blank=True, null=True)
    uri = models.CharField(max_length=255, blank=True, null=True,
        verbose_name='URI')

    domain = models.ManyToManyField('Type', blank=True, help_text="The domain"
                                    " specifies the resource types to which"
                                    " this Type or Field can apply. If no"
                                    " domain is specified, then this Type or"
                                    " Field can apply to any resource.")

    schema = models.ForeignKey('Schema', related_name='types', blank=True, null=True)
    parent = models.ForeignKey('Type', related_name='children', blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        try:
            return '%s (%s)' % (self.name, getattr(self.schema, '__unicode__', lambda: '')())
        except Schema.DoesNotExist:
            return self.name




class Field(models.Model):
    """
    A :class:`.Field` is a type for :class:`.Relation`\s.

    If range is null, can be applied to any Entity regardless of Type.
    """

    name = models.CharField(max_length=255)

    namespace = models.CharField(max_length=255, blank=True, null=True)
    uri = models.CharField(max_length=255, blank=True, null=True,
        verbose_name='URI')

    domain = models.ManyToManyField('Type', blank=True, help_text="The domain"
                                    " specifies the resource types to which"
                                    " this Type or Field can apply. If no"
                                    " domain is specified, then this Type or"
                                    " Field can apply to any resource.")

    schema = models.ForeignKey('Schema', related_name='fields', blank=True, null=True)

    parent = models.ForeignKey('Field', related_name='children', blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    range = models.ManyToManyField('Type', related_name='in_range_of',
                                   blank=True, help_text="The field's range"
                                   " specifies the resource types that are"
                                   " valid values for this field. If no range"
                                   " is specified, then this field will accept"
                                   " any value.")

    def __unicode__(self):
        try:
            return '%s (%s)' % (self.name, getattr(self.schema, '__unicode__', lambda: '')())
        except Schema.DoesNotExist:
            return self.name


### Values ###



class Value(models.Model):
    """
    Generic container for freeform data.

    Uses jsonpickle to support Python data types, as well as ``date`` and
    ``datetime`` objects.
    """

    _value = models.TextField()
    _type = models.CharField(max_length=255, blank=True, null=True)

    def _get_value(self):
        return jsonpickle.decode(self._value)

    def _set_value(self, value):
        self._type = type(value).__name__
        self._value = jsonpickle.encode(value)

    name = property(_get_value, _set_value)

    container = models.ForeignKey('ResourceContainer', blank=True, null=True)

    def __unicode__(self):
        return unicode(self.name)

    @property
    def uri(self):
        return u'Literal: ' + self.__unicode__()

    relations_from = GenericRelation('Relation',
                                     content_type_field='source_type',
                                     object_id_field='source_instance_id')

    relations_to = GenericRelation('Relation',
                                   content_type_field='target_type',
                                   object_id_field='target_instance_id')


### Relations ###


class Relation(Entity):
    """
    Defines a relationship beteween two :class:`Entity` instances.

    The :class:`.Entity` indicated by :attr:`.target` should fall within
    the range of the :class:`.Field` indicated by :attr:`.predicate`\. In other
    words, the :class:`.Type` of the target Entity should be listed in the
    predicate's :attr:`.Field.range` (unless the ``range`` is empty, in which
    case anything goes).
    """

    source_type = models.ForeignKey(ContentType, related_name='relations_from',
                                    on_delete=models.CASCADE)
    source_instance_id = models.PositiveIntegerField()
    source = GenericForeignKey('source_type', 'source_instance_id')

    predicate = models.ForeignKey('Field', related_name='instances',
                                  verbose_name='field')

    target_type = models.ForeignKey(ContentType, related_name='relations_to',
                                    on_delete=models.CASCADE, blank=True,
                                    null=True)
    target_instance_id = models.PositiveIntegerField(blank=True, null=True)
    target = GenericForeignKey('target_type', 'target_instance_id')

    data_source = models.CharField(max_length=1000, blank=True, null=True)

    sort_order = models.FloatField(default=0)

    class Meta:
        verbose_name = 'metadata relation'

        index_together = [
            ['source_type', 'source_instance_id'],
            ['target_type', 'target_instance_id'],
        ]

        # Unless otherwise specified, relations will be displayed in order of
        #  their creation (oldest first).
        ordering = ['id',]

    def save(self, *args, **kwargs):
        self.name = uuid4()
        super(Relation, self).save(*args, **kwargs)



class ConceptEntity(Entity):
    objects = models.Manager()
    active = ActiveManager()

    concept = models.ManyToManyField('concepts.Concept', blank=True)

    belongs_to = models.ForeignKey('Collection',
                                   related_name='native_conceptentities',
                                   blank=True, null=True)

    def get_absolute_url(self):
        return reverse('entity-details', args=(self.id,))

    def get_predicates(self):
        """
        Get information about all of the predicates for which this
        :class:`.ConceptEntity` instance has associated :class:`.Relation`\s.
        """
        fields = 'predicate_id', 'predicate__name', 'predicate__uri'
        raw = self.relations_from.order_by().values(*fields).distinct('predicate_id')
        return [{k.split('_')[-1]: v for k, v in d.iteritems()} for d in raw]


class Identity(models.Model):
    created_by = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)
    representative = models.ForeignKey('ConceptEntity',
                                       related_name='represents')
    entities = models.ManyToManyField('ConceptEntity',
                                      related_name='identities')


class ConceptType(Type):
    type_concept = models.ForeignKey('concepts.Type')


class UserJob(models.Model):
    """
    For tracking async jobs.
    """
    created_by = models.ForeignKey(User, related_name='jobs')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    result_id = models.CharField(max_length=255, null=True, blank=True)
    result = models.TextField()
    progress = models.FloatField(default=0.0)

    @property
    def percent(self):
        return self.progress * 100.

    def get_absolute_url(self):
        if self.result_id:
            return reverse('job-status', args=(self.result_id,))
        return reverse('jobs')


class GilesUpload(models.Model):
    upload_id = models.CharField(max_length=255, blank=True, null=True)
    resource = models.ForeignKey('Resource', related_name='giles_uploads',
                                 blank=True, null=True)
    """
    If the upload originated from Amphora, it should be associated with a
    :class:`.Resource` instance.
    """

    created_by = models.ForeignKey(User, related_name='giles_uploads')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    last_checked = models.DateTimeField(blank=True, null=True)

    PENDING = 'PD'
    ENQUEUED = 'EQ'
    SENT = 'ST'
    DONE = 'DO'
    SEND_ERROR = 'SE'
    GILES_ERROR = 'GE'
    PROCESS_ERROR = 'PE'
    CALLBACK_ERROR = 'CE'
    ASSIGNED = 'AS'     # A worker is polling this task.
    ERROR_STATES = (SEND_ERROR, GILES_ERROR, PROCESS_ERROR, CALLBACK_ERROR)
    OUTSTANDING = (ASSIGNED, ENQUEUED, SENT)
    STATES = (
        (PENDING, 'Pending'),      # Upload is ready to be dispatched.
        (ENQUEUED, 'Enqueued'),    # Dispatcher has created an upload task.
        (SENT, 'Sent'),            # File was sent successfully to Giles.
        (DONE, 'Done'),            # File was processed by Giles and Amphora.
        (SEND_ERROR, 'Send error'),    # Problem sending the file to Giles.
        (GILES_ERROR, 'Giles error'),  # Giles responded oddly after upload.
        (PROCESS_ERROR, 'Process error'),    # We screwed up post-processing.
        (CALLBACK_ERROR, 'Callback error'),  # Something went wrong afterwards.
        (ASSIGNED, 'Assigned')
    )
    state  = models.CharField(max_length=2, choices=STATES)

    PRIORITY_HIGH = 100
    PRIORITY_MEDIUM = 50
    PRIORITY_LOW = 10
    PRIORITIES = (
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_LOW, 'Low'),
    )
    priority = models.IntegerField(db_index=True, default=PRIORITY_LOW, choices=PRIORITIES)

    message = models.TextField()
    """Error messages, etc."""

    on_complete = models.TextField()
    """Serialized callback instructions."""

    file_path = models.TextField(blank=True, null=True)
    """Relative to MEDIA_ROOT."""


class GilesToken(models.Model):
    """
    A short-lived auth token for sending content to Giles on behalf of a user.

    See https://diging.atlassian.net/wiki/display/GIL/REST+Authentication.
    """

    for_user = models.OneToOneField(User, related_name='giles_token')
    created = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=255)


class ResourceContainer(models.Model):
    """
    Encapsulates a set of linked objects.
    """
    objects = models.Manager()
    active = ActiveManager()

    created_by = models.ForeignKey(User, related_name='containers', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    primary = models.ForeignKey('Resource', related_name='is_primary_for',
                                blank=True, null=True)

    part_of = models.ForeignKey('Collection', blank=True, null=True)
    is_deleted = models.BooleanField(default=False)


class CollectionAuthorization(models.Model):
    granted_by = models.ForeignKey(User, related_name='created_resource_auths')
    granted_to = models.ForeignKey(User, related_name='resource_resource_auths', blank=True, null=True)
    for_resource = models.ForeignKey('Collection', related_name='authorizations')
    heritable = models.BooleanField(default=True,
                                    help_text="Policy applies to all resources"
                                    " in this collection.")
    """
    If ``True``, this policy also applies to the :class:`.ResourceContainer`\s
    in the :class:`.Collection`\.
    """

    VIEW = 'VW'    # User can view the collection (list its contents).
    EDIT = 'ED'    # User can edit collection details.
    ADD = 'AD'     # User can add resources.
    REMOVE = 'RM'    # User can remove resources.
    SHARE = 'SH'     # User can share the collection with others.
    AUTH_ACTIONS = (
        (VIEW, 'View'),
        (EDIT, 'Edit'),
        (ADD, 'Add'),
        (REMOVE, 'Remove'),
        (SHARE, 'Share'),
    )
    action = models.CharField(choices=AUTH_ACTIONS, max_length=2)

    ALLOW = 'AL'
    DENY = 'DY'
    POLICIES = (
        (ALLOW, 'Allow'),
        (DENY, 'Deny'),
    )
    policy = models.CharField(choices=POLICIES, max_length=2)


class ResourceAuthorization(models.Model):
    granted_by = models.ForeignKey(User, related_name='created_collection_auths')
    granted_to = models.ForeignKey(User, related_name='resource_collection_auths', blank=True, null=True)
    for_resource = models.ForeignKey('ResourceContainer',
                                     related_name='authorizations')

    VIEW = 'VW'
    EDIT = 'ED'
    SHARE = 'SH'
    DELETE = 'DL'
    AUTH_ACTIONS = (
        (VIEW, 'View'),
        (EDIT, 'Edit'),
        (SHARE, 'Share'),
    )
    action = models.CharField(choices=AUTH_ACTIONS, max_length=2)

    ALLOW = 'AL'
    DENY = 'DY'
    POLICIES = (
        (ALLOW, 'Allow'),
        (DENY, 'Deny'),
    )
    policy = models.CharField(choices=POLICIES, max_length=2)


class Dataset(models.Model):
    created_by = models.ForeignKey(User, related_name='datasets')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=1000)
    description = models.TextField()

    resources = models.ManyToManyField('ResourceContainer', related_name='datasets')
    filter_parameters = models.TextField()

    EXPLICIT = 'EX'
    FILTER = 'FI'
    TYPES = (
        (EXPLICIT, 'Explicit'),
        (FILTER, 'Dynamic'),
    )
    dataset_type = models.CharField(max_length=2, choices=TYPES)


class DatasetSnapshot(models.Model):
    created_by = models.ForeignKey(User, related_name='snapshots')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    dataset = models.ForeignKey(Dataset, related_name='snapshots')
    has_content = models.BooleanField(default=True)
    has_metadata = models.BooleanField(default=False)
    content_type = models.CharField(max_length=255, blank=True, null=True)
    resource = models.OneToOneField(Resource, related_name='snapshot', blank=True, null=True)

    PENDING = 'PE'
    IN_PROGRESS = 'IP'
    DONE = 'DO'
    ERROR = 'ER'
    STATES = (
        (PENDING, 'Pending'),
        (IN_PROGRESS, 'In progress'),
        (DONE, 'Done'),
        (ERROR, 'Error')
    )
    state = models.CharField(max_length=2, choices=STATES, default=PENDING)
