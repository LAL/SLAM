# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('addr', models.CharField(max_length=40, blank=True)),
                ('macaddr', models.CharField(max_length=17, blank=True)),
                ('allocated', models.BooleanField(default=False)),
                ('date', models.DateTimeField(auto_now=True)),
                ('duration', models.DateTimeField(default=None, null=True, blank=True)),
                ('lastuse', models.DateTimeField(null=True, blank=True)),
                ('comment', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Alias',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('aliastype', models.CharField(default=b'name', max_length=4, choices=[(b'name', b'Name'), (b'addr', b'Address')])),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Config',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('conftype', models.CharField(max_length=6, choices=[(b'bind', b'Bind generator'), (b'rbind', b'Reverse look-up Bind generator'), (b'dhcp', b'ISC-DHCPd generator'), (b'quatt', b'Quattor generator'), (b'laldns', b'LAL DNS generator')])),
                ('default', models.BooleanField()),
                ('outputfile', models.TextField()),
                ('headerfile', models.TextField(null=True, blank=True)),
                ('footerfile', models.TextField(null=True, blank=True)),
                ('checkfile', models.TextField(null=True, blank=True)),
                ('name', models.CharField(max_length=50)),
                ('timeout', models.CharField(max_length=10, null=True, blank=True)),
                ('domain', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('category', models.CharField(max_length=20, blank=True)),
                ('serial', models.CharField(max_length=50, blank=True)),
                ('inventory', models.CharField(max_length=50, blank=True)),
                ('nodns', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='LogEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('author', models.CharField(max_length=255)),
                ('msg', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Pool',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, blank=True)),
                ('category', models.TextField(blank=True)),
                ('addr_range_type', models.CharField(max_length=5, choices=[(b'ip4', b'IPv4 subnet'), (b'ip6', b'IPv6 subnet'), (b'set', b'Address set')])),
                ('addr_range_str', models.TextField(blank=True)),
                ('dns_record', models.CharField(max_length=10)),
                ('generator', models.ManyToManyField(to='slam.Config')),
            ],
        ),
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=20)),
                ('value', models.TextField()),
                ('host', models.ForeignKey(blank=True, to='slam.Host', null=True)),
                ('pool', models.ForeignKey(blank=True, to='slam.Pool', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='alias',
            name='host',
            field=models.ForeignKey(to='slam.Host'),
        ),
        migrations.AddField(
            model_name='address',
            name='host',
            field=models.ForeignKey(blank=True, to='slam.Host', null=True),
        ),
        migrations.AddField(
            model_name='address',
            name='pool',
            field=models.ForeignKey(blank=True, to='slam.Pool', null=True),
        ),
        migrations.CreateModel(
            name='BindConfig',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('slam.config',),
        ),
        migrations.CreateModel(
            name='DhcpdConfig',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('slam.config',),
        ),
        migrations.CreateModel(
            name='LalDnsConfig',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('slam.config',),
        ),
        migrations.CreateModel(
            name='QuattorConfig',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('slam.config',),
        ),
        migrations.CreateModel(
            name='RevBindConfig',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('slam.config',),
        ),
    ]
