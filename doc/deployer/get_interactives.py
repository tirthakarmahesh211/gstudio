import requests
from bs4 import BeautifulSoup
from urlparse import urljoin
import csv

def get_interactives(base_url):
	header_data = ['thumbnail','file_name','resource_link','name','altnames','name_eng','collection','curricular','featured','content_org','description_eng','language','educationalalignment','educationalsubject','educationallevel','audience','educationaluse','interactivitytype','source','teaches','tags','basedonurl','prior_node','member_of','assesses','timerequired','textcomplexity','readinglevel','age_range','created_by','license','translation_of','adaptation_of','contributors']
	a_data = [header_data]
	page = requests.get(base_url)
	soup = BeautifulSoup(page.content, 'lxml')
	# sim_list_item = soup.select('td.simulation-list-item')
	# print(sim_list_item)
	thumbnails = soup.select('img.simulation-list-thumbnail')
	# print(thumbnails)
	tags = soup.select('span.simulation-list-title')
	# print(tags)
	links = soup.select('a.simulation-link')
	data = {}
	data['simulations'] = []
	meta_tag_content_list = []
	count = 1
	temp = True
	language = ('en', 'English')
	for thumbnail, tag, link in zip(thumbnails, tags, links):
		actual_data = []
		print(thumbnail['src'])
		print(thumbnail['src'].split("/")[-1])
		print(tag.text)
		# print(link)
		# break
		# data['simulations'].append(tuple([]))
		new_url = urljoin(base_url, link.get('href'))
		# print(new_url)
		new_page = requests.get(new_url)
		new_soup = BeautifulSoup(new_page.content, 'lxml')
		embeddable_text =new_soup.select('textarea#embeddable-text')
		meta_tag_content = new_soup.find('meta', attrs={'name':'description'})
		# meta_tag_content = meta_tag_content.select('meta')
		# meta_tag_content_list.append(meta_tag_content['content'])
		# print(meta_tag_content)
		# count = count + 1
		# print(count)
		# if count == 4:
		# break
		# print(meta_tag_content_list)
		# print(count)
		if embeddable_text[0].text.startswith("<iframe"):
			print(embeddable_text[0].text)
			resource_link = embeddable_text[0].text.split()[1][5:][:-1]
			print(resource_link)
			count = count + 1
			actual_data.insert(0,thumbnail['src'])
			actual_data.insert(1,thumbnail['src'].split("/")[-1])
			actual_data.insert(2,resource_link)
			actual_data.insert(3,tag.text)
			actual_data.insert(4,'')
			actual_data.insert(5,tag.text)
			actual_data.insert(6,'')
			actual_data.insert(7,'XCR')
			actual_data.insert(8,0)
			actual_data.insert(9,meta_tag_content['content'])
			actual_data.insert(10,'')
			actual_data.insert(11,language)
			actual_data.insert(12,"All")
			actual_data.insert(13,"")
			actual_data.insert(14,"")
			actual_data.insert(15,"")
			actual_data.insert(16,"Interactives")
			actual_data.insert(17,"Expositive")
			actual_data.insert(18,"PhET")
			actual_data.insert(19,"")
			actual_data.insert(20,tag.text)
			actual_data.insert(21,"")
			actual_data.insert(22,"")
			actual_data.insert(23,"")
			actual_data.insert(24,"")
			actual_data.insert(25,"")
			actual_data.insert(26,"")
			actual_data.insert(27,"")
			actual_data.insert(28,"")
			actual_data.insert(29,"")
			actual_data.insert(30,"")
			actual_data.insert(31,"")
			actual_data.insert(32,"")
			actual_data.insert(33,"")
			a_data.append(actual_data)
			print(a_data)
	with open('phet.csv', 'w') as csvFile:
		writer = csv.writer(csvFile)
		# if temp :
		# writer.writerow(header_data)
		# temp = False
		writer.writerows(a_data)
	csvFile.close()