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

nroer_team_id = 1
nroer_team_author_id = None

# setting variable:
# If set true, despite of having file nlob in gridfs, it fetches concern File which contains this _id in it's fs_file_ids field and returns it.
# If set False, returns None
update_file_exists_in_filehive = True

# INFO notes:
# http://172.16.0.252/sites/default/files/nroer_resources/ (for room no 012)
# http://192.168.1.102/sites/default/files/nroer_resources/ (for whole ncert campus)
# http://125.23.112.5/sites/default/files/nroer_resources/ (for public i.e outside campus)

resource_link_common = "http://125.23.112.5/sites/default/files/nroer_resources/"

class Command(BaseCommand):
    help = "\n\tFor saving data in gstudio DB from NROER schema files. This will create 'File' type GSystem instances.\n\tCSV file condition: The first row should contain DB names.\n"

    def handle(self, *args, **options):
        try:
            # print "working........" + SCHEMA_ROOT

            # processing each file of passed multiple CSV files as args
            for file_name in args:

                global csv_file_name
                csv_file_name = file_name
                print csv_file_name
                file_path = os.path.join(SCHEMA_ROOT, file_name)

                if os.path.exists(file_path):

                    file_extension = os.path.splitext(file_name)[1]

                    if "csv" in file_extension:

                        total_rows = 0

                        # Process csv file and convert it to json format at first
                        info_message = "\n- CSV File (" + file_path + ") found!!!"
                        print info_message
                        log_list.append(str(info_message))

                        try:
                            csv_file_path = file_path
                            json_file_name = file_name.rstrip("csv") + "json"
                            json_file_path = os.path.join(SCHEMA_ROOT, json_file_name)
                            json_file_content = ""

                            with open(csv_file_path, 'rb') as csv_file:
                                csv_file_content = csv.DictReader(csv_file, delimiter=",")
                                json_file_content = []

                                for row in csv_file_content:
                                    total_rows += 1
                                    json_file_content.append(row)

                                info_message = "\n- File '" + file_name + "' contains : [ " + str(total_rows) + " ] entries/rows (excluding top-header/column-names)."
                                print info_message
                                log_list.append(str(info_message))

                            with open(json_file_path, 'w') as json_file:
                                json.dump(json_file_content, json_file, indent=4, sort_keys=False)

                            if os.path.exists(json_file_path):
                                file_path = json_file_path
                                is_json_file_exists = True
                                info_message = "\n- JSONType: File (" + json_file_path + ") created successfully.\n"
                                print info_message
                                log_list.append(str(info_message))

                        except Exception as e:
                            error_message = "\n!! CSV-JSONError: " + str(e)
                            print error_message
                            log_list.append(str(error_message))
                            # End of csv-json coversion

                    elif "json" in file_extension:
                        is_json_file_exists = True

                    else:
                        error_message = "\n!! FileTypeError: Please choose either 'csv' or 'json' format supported files!!!\n"
                        print error_message
                        log_list.append(str(error_message))
                        raise Exception(error_mesage)

                    if is_json_file_exists:

                        # create_user_nroer_team()
                        # print nroer_team_id

                        # Process json file and create required GSystems, GRelations, and GAttributes
                        info_message = "\n------- Initiating task of processing json-file -------\n"
                        print info_message
                        log_list.append(str(info_message))

                        t0 = time.time()
                        parse_data_create_gsystem(file_path)
                        t1 = time.time()

                        time_diff = t1 - t0
                        total_time_minute = round( (time_diff/60), 2) if time_diff else 0
                        total_time_hour = round( (time_diff/(60*60)), 2) if time_diff else 0

                        # End of processing json file

                        info_message = "\n------- Task finised: Successfully processed json-file -------\n"
                        info_message += "- Total time taken for the processing: \n\n\t" + str(total_time_minute) + " MINUTES\n\t=== OR ===\n\t" + str(total_time_hour) + " HOURS\n"
                        print info_message
                        log_list.append(str(info_message))
                        # End of creation of respective GSystems, GAttributes and GRelations for Enrollment

                else:
                    error_message = "\n!! FileNotFound: Following path (" + file_path + ") doesn't exists!!!\n"
                    print error_message
                    log_list.append(str(error_message))
                    raise Exception(error_message)

        except Exception as e:
            print str(e)
            log_list.append(str(e))

        finally:
            if log_list:

                log_list.append("\n ============================================================ End of Iteration ============================================================\n\n\n")
                # print log_list

                log_file_name = args[0].rstrip("csv") + "log"
                log_file_path = os.path.join(SCHEMA_ROOT, log_file_name)
                # print log_file_path
                with open(log_file_path, 'a') as log_file:
                    log_file.writelines(log_list)

            if log_file_not_found != [script_start_str]:

                log_file_not_found.append("============================== End of Iteration =====================================\n")
                log_file_not_found.append("-------------------------------------------------------------------------------------\n")

                log_file_name = args[0].replace('.', '_FILES_NOT_FOUND.').rstrip("csv") + "log"
                log_file_path = os.path.join(SCHEMA_ROOT, log_file_name)
                # print log_file_path
                with open(log_file_path, 'a') as log_file:
                    log_file.writelines(log_file_not_found)

            if log_error_rows != [script_start_str]:

                log_error_rows.append("============================== End of Iteration =====================================\n")
                log_error_rows.append("-------------------------------------------------------------------------------------\n")

                log_file_name = args[0].replace('.', '_ERROR_ROWS.').rstrip("csv") + "log"
                log_file_path = os.path.join(SCHEMA_ROOT, log_file_name)
                # print log_file_path
                with open(log_file_path, 'a') as log_file:
                    log_file.writelines(log_error_rows)

    # --- End of handle() ---


def log_print(log_string):
    try:
        log_list.append(log_string)
        print log_string

    except:
        error_message = '\n !! Error while doing log and print.\n\n'
        print error_message
        log_list.append(error_message)

def parse_data_create_gsystem(json_file_path):
    json_file_content = ""

    try:
        with open(json_file_path) as json_file:
            json_file_content = json_file.read()

        json_documents_list = json.loads(json_file_content)

        # Initiating empty node obj and other related data variables
        node = node_collection.collection.GSystem()
        node_keys = node.keys()
        node_structure = node.structure
        # print "\n\n---------------", node_keys

        json_documents_list_spaces = json_documents_list
        json_documents_list = []

        # Removes leading and trailing spaces from keys as well as values
        for json_document_spaces in json_documents_list_spaces:
            json_document = {}

            for key_spaces, value_spaces in json_document_spaces.iteritems():
                json_document[key_spaces.strip().lower()] = value_spaces.strip()

            json_documents_list.append(json_document)

    except Exception as e:
        error_message = "\n!! While parsing the file ("+json_file_path+") got following error...\n " + str(e)
        log_print(error_message)
        raise error_message
    count_for_desc = 0
    count_for_lang = 0
    for i, json_document in enumerate(json_documents_list):

        info_message = "\n\n\n********** Processing row number : ["+ str(i + 2) + "] **********"
        log_print(info_message)
        parsed_json_document = {}
        attribute_relation_list = []
        boolean = False
        # try:
        for key in json_document.iterkeys():
            parsed_key = key.lower()
            # print json_document.get("filename")
            # a = node_collection.find_one({"attribute_set.name_eng":json_document.get("name_eng")})
            a = node_collection.find_one({"name":json_document.get("name")})
            if True:
                # print json_document.get("name")
                if a:
                    print a._id
                    if a.content in (None,'',"") or a.content_org in (None,'',""):
                        # print a
                        # print a["_id"]
                        print "==========================================content"
                        boolean = True
                        # break;
                        # json_document.get("language")
                        a.update({"content":json_document.get("content_org")})
                        a.update({"content_org":json_document.get("content_org")})
                        # a.save()
                        # esearch.save_to_es(a)
                        count_for_desc = count_for_desc + 1
                        print count_for_desc
                        content = True
                    if a.language[0] != json_document.get("language")[2:4]:
                        if a.language[0].lower() == "hi" or a.language[0].lower() == "en":
                            boolean = True
                            print json_document.get("language")
                            print a.language
                            print "Old Metadata of language field is :"+ a.language[0]
                            print "New Metadata of language field is :"+ json_document.get("language")[2:4]
                            print "The language field is updated with " + a.language[0] + " to " + json_document.get("language")[2:4]
                            count_for_lang = count_for_lang + 1
                            language  = True
                            print count_for_lang
                    if language or content : 
                        a.save()
                        esearch.save_to_es(a)
                    break;
        if boolean :
            break;
        # except:
        #     pass
