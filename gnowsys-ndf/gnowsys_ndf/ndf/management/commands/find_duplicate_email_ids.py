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
from gnowsys_ndf.settings import GSTUDIO_SITE_NAME
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


class Command(BaseCommand):

    def handle(self, *args, **options):

        if GSTUDIO_SITE_NAME == "NROER":
            all_users=[]
            with open("/home/docker/code/gstudio/gnowsys-ndf/email_ids.log", 'a+') as log_file:
                for each in User.objects.all():
                    if each.email:
                        all_users.append(each.email)
                        log_file.writelines(each.email)
                        log_file.writelines("\n")

        if GSTUDIO_SITE_NAME != "NROER":
            total_users = node_collection.find({"_type":"Author"})
            print total_users.count()
            duplicate_email_id_list = []
            duplicate_email_id_count = 0
            print "Processing.............."
            i = 0
            for each in total_users:
                try:
                    print each.email
                    if each:
                        if each.email:
                            # print each.email
                            user_info = node_collection.find_one({"email":each.email})
                            # if user_info.count() > 1:
                except:
                    i= i + 1
                    print "DUPLICATE EMAIL ID FOOUND"
                    # print duplicate_email_id_list
                    duplicate_email_id_list.append(each.email)
                    duplicate_email_id_count = duplicate_email_id_count + 1
                    print each.email
                    if i > 1:
                        break;
            print total_users.count()
            print duplicate_email_id_count