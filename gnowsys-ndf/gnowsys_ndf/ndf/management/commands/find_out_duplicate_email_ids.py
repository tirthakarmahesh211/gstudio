''' imports from python libraries '''
import os
import csv
import json
import datetime
import urllib2
import hashlib
import io
import time

# import ast
# import magic
# import subprocess
# import mimetypes
# from PIL import Image
# from StringIO import StringIO

''' imports from installed packages '''
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.http import HttpRequest
# from django.core.management.base import CommandError

from django_mongokit import get_database
from mongokit import IS

try:
    from bson import ObjectId
except ImportError:  # old pymongo
    from pymongo.objectid import ObjectId

''' imports from application folders/files '''
from gnowsys_ndf.ndf.models import Node, Filehive, gfs
from gnowsys_ndf.ndf.models import GSystemType, AttributeType, RelationType
from gnowsys_ndf.ndf.models import GSystem, GAttribute, GRelation
from gnowsys_ndf.ndf.models import node_collection, triple_collection, gridfs_collection, filehive_collection
# from gnowsys_ndf.ndf.models import node_collection
# from gnowsys_ndf.ndf.views.file import save_file
from gnowsys_ndf.ndf.views.methods import create_grelation, create_gattribute, get_language_tuple
from gnowsys_ndf.ndf.management.commands.create_theme_topic_hierarchy import add_to_collection_set
from gnowsys_ndf.ndf.views.tasks import convertVideo
from gnowsys_ndf.ndf.gstudio_es.es import *
##############################################################################

SCHEMA_ROOT = os.path.join(os.path.dirname(__file__), "schema_files")
csv_file_name = None

script_start_str = "######### Script ran on : " + time.strftime("%c") + " #########\n------------------------------------------------------------\n"
log_file_not_found = []
log_file_not_found.append(script_start_str)

log_list = []  # To hold intermediate errors
log_list.append(script_start_str)

log_error_rows = []
log_error_rows.append(script_start_str)

file_gst = node_collection.one({'_type': 'GSystemType', "name": "File"})
auth_gst = node_collection.one({'_type': u'GSystemType', 'name': u'Author'})
home_group = node_collection.one({"name": "home", "_type": "Group"})
warehouse_group = node_collection.one({"name": 'warehouse', "_type": "Group"})
theme_gst = node_collection.one({'_type': 'GSystemType', "name": "Theme"})
theme_item_gst = node_collection.one({'_type': 'GSystemType', "name": "theme_item"})
topic_gst = node_collection.one({'_type': 'GSystemType', "name": "Topic"})
twist_gst = node_collection.one({'_type': 'GSystemType', 'name': 'Twist'})
rel_resp_at = node_collection.one({'_type': 'AttributeType', 'name': 'release_response'})
thr_inter_type_at = node_collection.one({'_type': 'AttributeType', 'name': 'thread_interaction_type'})
has_thread_rt = node_collection.one({"_type": "RelationType", "name": u"has_thread"})
has_thumbnail_rt = node_collection.one({'_type': "RelationType", 'name': u"has_thumbnail"})
discussion_enable_at = node_collection.one({"_type": "AttributeType", "name": "discussion_enable"})

class Command(BaseCommand):

    def handle(self, *args, **options):

        total_users = node_collection.find({"_type":"Author"})
        print total_users.count()
        duplicate_email_id_list = []
        duplicate_email_id_count = 0
        print "Processing.............."
        for each in total_users:
            try:
                print ".."
                print each.email
                if each:
                    if each.email:
                        # print each.email
                        user_info = node_collection.find_one({"email":each.email})
                        # if user_info.count() > 1:
            except:
                print "DUPLICATE EMAIL ID FOOUND"
                # print duplicate_email_id_list
                duplicate_email_id_list.append(each.email)
                duplicate_email_id_count = duplicate_email_id_count + 1
                print each.email
        print total_users.count()
        print duplicate_email_id_count