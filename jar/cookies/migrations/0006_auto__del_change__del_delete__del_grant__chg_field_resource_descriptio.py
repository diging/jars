# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Change'
        db.delete_table(u'cookies_change')

        # Deleting model 'Delete'
        db.delete_table(u'cookies_delete')

        # Deleting model 'Grant'
        db.delete_table(u'cookies_grant')


        # Changing field 'Resource.description'
        db.alter_column(u'cookies_resource', 'description', self.gf('django.db.models.fields.TextField')(null=True))
        # Adding unique constraint on 'Action', fields ['type']
        db.create_unique(u'cookies_action', ['type'])

        # Adding field 'Schema.name'
        db.add_column(u'cookies_schema', 'name',
                      self.gf('django.db.models.fields.CharField')(default='bob', max_length=200),
                      keep_default=False)


    def backwards(self, orm):
        # Removing unique constraint on 'Action', fields ['type']
        db.delete_unique(u'cookies_action', ['type'])

        # Adding model 'Change'
        db.create_table(u'cookies_change', (
            (u'action_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cookies.Action'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'cookies', ['Change'])

        # Adding model 'Delete'
        db.create_table(u'cookies_delete', (
            (u'action_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cookies.Action'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'cookies', ['Delete'])

        # Adding model 'Grant'
        db.create_table(u'cookies_grant', (
            (u'action_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cookies.Action'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'cookies', ['Grant'])


        # User chose to not deal with backwards NULL issues for 'Resource.description'
        raise RuntimeError("Cannot reverse this migration. 'Resource.description' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'Resource.description'
        db.alter_column(u'cookies_resource', 'description', self.gf('django.db.models.fields.TextField')())
        # Deleting field 'Schema.name'
        db.delete_column(u'cookies_schema', 'name')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'cookies.action': {
            'Meta': {'object_name': 'Action'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '2'})
        },
        u'cookies.authority': {
            'Meta': {'object_name': 'Authority'},
            'endpoint': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'namespace': ('django.db.models.fields.TextField', [], {})
        },
        u'cookies.authorization': {
            'Meta': {'object_name': 'Authorization'},
            'actor': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'on': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cookies.Entity']"}),
            'to_do': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cookies.Action']"})
        },
        u'cookies.corpus': {
            'Meta': {'object_name': 'Corpus', '_ormbases': [u'cookies.Resource']},
            u'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cookies.Resource']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cookies.datetimevalue': {
            'Meta': {'object_name': 'DateTimeValue', '_ormbases': [u'cookies.Value']},
            'value': ('django.db.models.fields.DateTimeField', [], {}),
            u'value_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cookies.Value']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cookies.entity': {
            'Meta': {'object_name': 'Entity'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        u'cookies.entityrelation': {
            'Meta': {'object_name': 'EntityRelation', '_ormbases': [u'cookies.FieldRelation']},
            u'fieldrelation_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cookies.FieldRelation']", 'unique': 'True', 'primary_key': 'True'}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'relations_to'", 'to': u"orm['cookies.Entity']"})
        },
        u'cookies.event': {
            'Meta': {'object_name': 'Event'},
            'by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'did': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cookies.Action']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'occurred': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'on': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cookies.Entity']"})
        },
        u'cookies.field': {
            'Meta': {'object_name': 'Field'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        u'cookies.fieldrelation': {
            'Meta': {'object_name': 'FieldRelation'},
            'field': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cookies.Field']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'relations_from'", 'to': u"orm['cookies.Entity']"})
        },
        u'cookies.floatvalue': {
            'Meta': {'object_name': 'FloatValue', '_ormbases': [u'cookies.Value']},
            'value': ('django.db.models.fields.FloatField', [], {}),
            u'value_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cookies.Value']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cookies.integervalue': {
            'Meta': {'object_name': 'IntegerValue', '_ormbases': [u'cookies.Value']},
            'value': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'value_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cookies.Value']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cookies.localresource': {
            'Meta': {'object_name': 'LocalResource', '_ormbases': [u'cookies.Resource']},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cookies.Resource']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cookies.remoteresource': {
            'Meta': {'object_name': 'RemoteResource', '_ormbases': [u'cookies.Resource']},
            u'resource_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cookies.Resource']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '2000'})
        },
        u'cookies.resource': {
            'Meta': {'object_name': 'Resource', '_ormbases': [u'cookies.Entity']},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'entity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cookies.Entity']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cookies.schema': {
            'Meta': {'object_name': 'Schema'},
            'fields': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['cookies.Field']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'cookies.textvalue': {
            'Meta': {'object_name': 'TextValue', '_ormbases': [u'cookies.Value']},
            'value': ('django.db.models.fields.TextField', [], {}),
            u'value_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cookies.Value']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cookies.value': {
            'Meta': {'object_name': 'Value'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'cookies.valuerelation': {
            'Meta': {'object_name': 'ValueRelation', '_ormbases': [u'cookies.FieldRelation']},
            u'fieldrelation_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cookies.FieldRelation']", 'unique': 'True', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cookies.Value']"})
        }
    }

    complete_apps = ['cookies']