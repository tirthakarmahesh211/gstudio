import re
import urllib

''' -- imports from installed packages -- '''
from django.shortcuts import render_to_response
from django.template import RequestContext
from mongokit import paginator

try:
	from bson import ObjectId
except ImportError:  # old pymongo
	from pymongo.objectid import ObjectId

''' -- imports from application folders/files -- '''
from gnowsys_ndf.settings import GAPPS
# from gnowsys_ndf.ndf.models import Node, GRelation,GSystemType,File,Triple
from gnowsys_ndf.ndf.models import Node, GRelation,GSystemType, Triple
from gnowsys_ndf.ndf.models import node_collection,GSystemType
from gnowsys_ndf.ndf.views.file import *
from gnowsys_ndf.ndf.views.methods import get_group_name_id, cast_to_data_type, get_execution_time
from gnowsys_ndf.ndf.views.methods import get_filter_querydict
from gnowsys_ndf.ndf.gstudio_es.es import *
from gnowsys_ndf.ndf.gstudio_es.paginator import Paginator ,EmptyPage, PageNotAnInteger
from gnowsys_ndf.ndf.templatetags.ndf_tags import get_relation_value
from gnowsys_ndf.settings import GSTUDIO_ELASTIC_SEARCH
from django.core.exceptions import PermissionDenied

def search_detail(request,group_id,page_num=1):
	if GSTUDIO_ELASTIC_SEARCH:
		# if not request.user.is_superuser:
		# 	raise PermissionDenied
		q = Q('match',name=dict(query='File',type='phrase'))
		GST_FILE = Search(using=es, index="nodes",doc_type="gsystemtype").query(q)
		GST_FILE1 = GST_FILE.execute()

		q = Q('match',name=dict(query='Page',type='phrase'))
		GST_PAGE = Search(using=es, index="nodes",doc_type="gsystemtype").query(q)
		GST_PAGE1 = GST_PAGE.execute()

		q = Q('match',name=dict(query='interactive_page',type='phrase'))
		GST_IPAGE = Search(using=es, index="nodes",doc_type="gsystemtype").query(q)
		GST_IPAGE1 = GST_IPAGE.execute()

		search_result = ''
		try:
			group_id = ObjectId(group_id)

		except:
			group_name, group_id = get_group_name_id(group_id)

		group_name_of_twist, group_id_of_twist = GSystemType.get_gst_name_id("Twist")
		group_name_of_file, group_id_of_file = GSystemType.get_gst_name_id("File")
		group_name_of_page, group_id_of_page = GSystemType.get_gst_name_id("Page")
		chk_advanced_search = request.GET.get('chk_advanced_search',None)

		if request.GET.get('field_list',None):
			selected_field = request.GET.get('field_list',None)
			# print selected_field
		else:
			selected_field = "content"
		english_lang = False
		temp_list = []
		edu_subject = request.GET.get('edu_subject',None)
		# print "====================================================="
		# print edu_subject
		# print "====================================================="
		if selected_field == "english_lang":
			english_lang = True
			from bs4 import BeautifulSoup
			print "english_lang"
			if edu_subject:
				q = Q('bool', must=[Q('match',attribute_set__educationalsubject=edu_subject),Q('match',group_set=str(group_id)),Q('match',access_policy='public'),Q('match',language='en')],
					should=[Q('match', member_of=GST_FILE1.hits[0].id),Q('match', member_of=GST_IPAGE1.hits[0].id),Q('match', member_of=GST_PAGE1.hits[0].id)]
					,minimum_should_match=1)
			else:
				q = Q('bool', must=[Q('match',group_set=str(group_id)),Q('match',access_policy='public'),Q('match',language='en')],
					should=[Q('match', member_of=GST_FILE1.hits[0].id),Q('match', member_of=GST_IPAGE1.hits[0].id),Q('match', member_of=GST_PAGE1.hits[0].id)]
					,minimum_should_match=1)
			search_result =Search(using=es, index="nodes",doc_type="gsystemtype,gsystem,metatype,relationtype,attribute_type,group,author").query(q)
			page_no = request.GET.get('page_no',None)
			has_next = True
			if search_result.count() <=20:
				has_next = False

			if request.GET.get('page_no',None) in [None,'']:
				search_result=search_result[0:20]
				page_no = 2
			else:
				p = int(int(page_no) -1)
				temp1=int((int(p)) * 20)
				temp2=temp1+20
				search_result=search_result[temp1:temp2]

				if temp1 < search_result.count() <= temp2:
					has_next = False
				page_no = int(int(page_no)+1)	
			print search_result.count()
			e_search_result = search_result.execute()
			from langdetect import detect
			i = 1
			for temp in e_search_result["hits"]["hits"]:
				print "for loop"
				try:
					content_lang = temp["_source"].content
					content_org_lang = temp["_source"].content_org

					if content_lang:
						content_lang = content_lang.decode("utf-8")
						content_lang = BeautifulSoup(content_lang, "lxml").text
						if detect(content_lang) == "hi":
							# print detect(content_lang)
							# print detect(content_org_lang)
							# print temp["_source"].id
							temp_list.append(temp["_source"])
							# print temp_list
					if content_org_lang:
						content_org_lang = content_org_lang.decode("utf-8")
						content_org_lang = BeautifulSoup(content_org_lang, "lxml").text
						if detect(content_org_lang) == "hi":
							temp_list.append(temp["_source"])
							# print temp_list

					if i > 19:
						break;
					i = i + 1
				except:
					pass
		elif selected_field == "hindi_lang":
			english_lang = True
			from bs4 import BeautifulSoup
			print "hindi_lang"
			if edu_subject:
				q = Q('bool', must=[Q('match',attribute_set__educationalsubject=edu_subject),Q('match',group_set=str(group_id)),Q('match',access_policy='public'),Q('match',language='hi')],
					should=[Q('match', member_of=GST_FILE1.hits[0].id),Q('match', member_of=GST_IPAGE1.hits[0].id),Q('match', member_of=GST_PAGE1.hits[0].id)]
					,minimum_should_match=1)
			else:
				q = Q('bool', must=[Q('match',group_set=str(group_id)),Q('match',access_policy='public'),Q('match',language='hi')],
					should=[Q('match', member_of=GST_FILE1.hits[0].id),Q('match', member_of=GST_IPAGE1.hits[0].id),Q('match', member_of=GST_PAGE1.hits[0].id)]
					,minimum_should_match=1)
			search_result =Search(using=es, index="nodes",doc_type="gsystemtype,gsystem,metatype,relationtype,attribute_type,group,author").query(q)
			page_no = request.GET.get('page_no',None)
			has_next = True
			if search_result.count() <=20:
				has_next = False

			if request.GET.get('page_no',None) in [None,'']:
				search_result=search_result[0:20]
				page_no = 2
			else:
				p = int(int(page_no) -1)
				temp1=int((int(p)) * 20)
				temp2=temp1+20
				search_result=search_result[temp1:temp2]

				if temp1 < search_result.count() <= temp2:
					has_next = False
				page_no = int(int(page_no)+1)
			print search_result.count()
			e_search_result = search_result.execute()
			from langdetect import detect
			i = 1
			for temp in e_search_result["hits"]["hits"]:
				print "for loop"
				try:
					content_lang = temp["_source"].content
					content_org_lang = temp["_source"].content_org

					if content_lang:
						content_lang = content_lang.decode("utf-8")
						content_lang = BeautifulSoup(content_lang, "lxml").text
						if detect(content_lang) == "en":
							# print detect(content_lang)
							# print detect(content_org_lang)
							# print temp["_source"].id
							temp_list.append(temp["_source"])
							# print temp_list
					if content_org_lang:
						content_org_lang = content_org_lang.decode("utf-8")
						content_org_lang = BeautifulSoup(content_org_lang, "lxml").text
						if detect(content_org_lang) == "en":
							temp_list.append(temp["_source"])
							# print temp_list
					if i > 19:
						break;
					i = i + 1
				except:
					pass

		else:
			print "else block"
			if edu_subject:
				q = Q('bool', must=[Q('match',attribute_set__educationalsubject=edu_subject),Q('terms',attribute_set__educationaluse=['documents','images','audios','videos','interactives','ebooks']),Q('match',group_set=str(group_id)),Q('match',access_policy='public'),~Q('exists',field=selected_field)],
				should=[Q('match', member_of=GST_FILE1.hits[0].id),Q('match', member_of=GST_IPAGE1.hits[0].id),Q('match', member_of=GST_PAGE1.hits[0].id)])
			else:
				q = Q('bool', must=[Q('terms',attribute_set__educationaluse=['documents','images','audios','videos','interactives','ebooks']),Q('match',group_set=str(group_id)),Q('match',access_policy='public'),~Q('exists',field=selected_field)],
				should=[Q('match', member_of=GST_FILE1.hits[0].id),Q('match', member_of=GST_IPAGE1.hits[0].id),Q('match', member_of=GST_PAGE1.hits[0].id)])
			# must_not=[Q('match', member_of=GST_PAGE1.hits[0].id)])
			search_result =Search(using=es, index="nodes",doc_type="gsystemtype,gsystem,metatype,relationtype,attribute_type,group,author").query(q)
			# search_result = search_result.exclude('terms', name=['thumbnail','jpg','png','svg'])
			print search_result.count()
		count = ""
		count = search_result.count()
		if request.GET.get('field_list',None) == "true":

			search_text = request.GET.get("search_text",None)
			if edu_subject:
				q = Q('bool', must=[Q('match',attribute_set__educationalsubject=edu_subject),Q('match', language='en'),Q('match', access_policy='public'),Q('match', group_set=str(group_id)),
					Q('terms', content=[search_text])] )
			else:
				q = Q('bool', must=[Q('match', language='en'),Q('match', access_policy='public'),Q('match', group_set=str(group_id)),
					Q('terms', content=[search_text])] )
			search_result =Search(using=es, index="nodes",doc_type="gsystemtype,gsystem,metatype,relationtype,attribute_type,group,author").query(q)

		if_teaches = False
		search_str_user=""
		page_no = request.GET.get('page_no',None)
		has_next = True
		if search_result.count() <=20:
			has_next = False

		if request.GET.get('page_no',None) in [None,'']:
			search_result=search_result[0:20]
			page_no = 2
		else:
			p = int(int(page_no) -1)
			temp1=int((int(p)) * 20)
			temp2=temp1+20
			search_result=search_result[temp1:temp2]

			if temp1 < search_result.count() <= temp2:
				has_next = False
			page_no = int(int(page_no)+1)
		paginator_search_result = None

		if request.GET.get('field_list',None) == "attribute_type_set" or page_num > 1 :
			temp = node_collection.find({"attribute_set.educationaluse":{'$in':["Audios","Videos","eBooks","Interactives","Images","Documents"]},'_type': 'GSystem','access_policy':'PUBLIC','member_of': { '$in': [ObjectId(group_id_of_file),ObjectId(group_id_of_page)] } ,'group_set':ObjectId(group_id)}).limit(1000)

			lst = []
			for each in temp:
			    if each._id:
			        rel_val = get_relation_value(ObjectId(each._id),"teaches")
			        if not rel_val['grel_id']:
						lst.append(each._id)

			search_result = node_collection.find({ '_id': {'$in': lst} }).limit(1000)
			if_teaches = True
			paginator_search_result = paginator.Paginator(search_result, page_num, 30)
			count = search_result.count()
		# print temp_list
		if temp_list :
			# print "temp_list-----------------------------------"
			search_result = temp_list
		elif temp_list in (None,"",'',False,[]) and english_lang == True:
			search_result = ""


		if selected_field == "content":
			applied_filter_name = "The resources that do not have any description"
		elif selected_field == "tags":
			applied_filter_name = "The resources that do not have any tags"
		elif selected_field == "location":
			applied_filter_name = "The resources that do not have any location"
		elif selected_field == "english_lang":
			applied_filter_name = "The resources that are actually Hindi, but the language was set to English"
		elif selected_field == "hindi_lang":
			applied_filter_name = "The resources that have English description, but the resource is in Hindi language"
		elif selected_field == "attribute_type_set":
			applied_filter_name = "The resources that do not have 'teaches' relation set to any topic"

		return render_to_response('ndf/asearch.html', {"applied_filter_name":applied_filter_name,"count":count,"english_lang":english_lang,"page_info":paginator_search_result,"page_no":page_no,"has_next":has_next,'GSTUDIO_ELASTIC_SEARCH':GSTUDIO_ELASTIC_SEARCH,'advanced_search':"true",'groupid':group_id,'group_id':group_id,'title':"advanced_search","search_curr":search_result,'field_list':selected_field,'chk_advanced_search':chk_advanced_search,'if_teaches':if_teaches},
					context_instance=RequestContext(request))

