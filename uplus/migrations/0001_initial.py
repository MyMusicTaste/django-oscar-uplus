# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UplusTransaction'
        db.create_table(u'uplus_uplustransaction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('amount', self.gf('django.db.models.fields.IntegerField')(default=0, null=True, blank=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='N', max_length=1, db_index=True)),
            ('basket_id', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('order_number', self.gf('django.db.models.fields.CharField')(max_length=128, db_index=True)),
            ('pay_key', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('pay_type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('tid', self.gf('django.db.models.fields.CharField')(max_length=24, blank=True)),
            ('financode', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('financename', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('financeauth', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('cashreceipt', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('error_message', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('error_code', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
        ))
        db.send_create_signal('uplus', ['UplusTransaction'])


    def backwards(self, orm):
        # Deleting model 'UplusTransaction'
        db.delete_table(u'uplus_uplustransaction')


    models = {
        'uplus.uplustransaction': {
            'Meta': {'ordering': "('-id',)", 'object_name': 'UplusTransaction'},
            'amount': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'basket_id': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cashreceipt': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'error_code': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'error_message': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'financeauth': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'financename': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'financode': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order_number': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'pay_key': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'pay_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1', 'db_index': 'True'}),
            'tid': ('django.db.models.fields.CharField', [], {'max_length': '24', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['uplus']