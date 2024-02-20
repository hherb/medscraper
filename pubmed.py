import os
import requests
import json
from datetime import datetime

def fetch_medrxiv_publications(start_date, end_date=None, server='medrxiv'):
	"""
	Fetches a list of publications from medrxiv from start_date to end_date
	
	:param start_date: format yyy-mm-dd
	:param end_date: format yyy-mm-dd
	:return: List of publication dicts fetched from the medRxiv API.
	The following metadata elements are returned as strings in the dict:
		doi
		title
		authors
		author_corresponding
		author_corresponding_institution
		date
		version
		type
		license
		category
		jats xml path
		abstract
		published
		server
	"""
	if not end_date:
		end_date = datetime.now().strftime("%Y-%m-%d") #today
		
	base_url = f"https://api.medrxiv.org/details/{server}/{start_date}/{end_date}"
	cursor = 0
	all_results = []

	while True:
		url = f"{base_url}/{cursor}/json"
		response = requests.get(url)
		data = response.json()

		publications = data.get('collection', [])
		all_results.extend(publications)

		# Check if more results are available
		messages = data.get('messages', [])
		if messages:
			message = messages[0]
			total_items = message.get('count', 0)
			if cursor + len(publications) >= total_items:
				break  # No more results
			cursor += len(publications)
		else:
			break  # No messages, likely no more results

	return all_results
 
	
def screen_publications_by_keywords(publications, keywords):
	"""
	Screens a list of publications for specified keywords in the title or abstract.

	:param publications: List of publication dicts fetched from the medRxiv API.
	:param keywords: List of keywords to search for in the title and abstract.
	:return: List of publication dicts that contain any of the keywords in their title or abstract.
	"""
	filtered_publications = []
	keywords_lower = [keyword.lower() for keyword in keywords]

	for publication in publications:
		title = publication.get('title', '').lower()
		abstract = publication.get('abstract', '').lower()

		# Check if any of the keywords appear in the title or abstract
		if any(keyword in title or keyword in abstract for keyword in keywords_lower):
			filtered_publications.append(publication)

	return filtered_publications


def download_pdf(publication, output_dir = "./pdf"):
	"""download the corresponding pdf file for a given medRxiv publication in dict format"""
	
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)

	title = publication.get('title', '')
	pdf_url = "https://www.medrxiv.org/content/" + publication.get("doi", '') + ".full.pdf"
	pdf_filename = f"{output_dir}/{title}.pdf"

	try:
		response = requests.get(pdf_url)
		if response.status_code == 200:
			with open(pdf_filename, "wb") as pdf_file:
				pdf_file.write(response.content)
				print(f"Downloaded: {title}.pdf")
		else:
			print(f"Failed to download: {title}.pdf")
	except Exception as e:
		print(f"Error downloading {title}.pdf: {e}")
		

# Example usage
start_date = "2024-02-12"
#end_date = "2024-02-19"
publications = fetch_medrxiv_publications(start_date)

keywords = ["GPT4", "machine learning", "deep learning", "large language model", "Anthropic", "OpenAI", "Artifical Intelligence"]
filtered_publications = screen_publications_by_keywords(publications, keywords)


# Print the titles and DOIs of the fetched publications
for publication in filtered_publications:
	print(f"\nTitle: {publication['title']}")
	print(f"\nAuthors: {publication['authors']}")
	print(f"\nDOI: {publication['doi']}")
	print(f"\nPublication Date: {publication['date']}")
	print(f"\nAbstract: {publication['abstract']}")

	print("\n=========================================================================\n")
	download_pdf(publication)

# Optionally, save the results to a file
with open('new_medrxiv_publications.json', 'w') as f:
	json.dump(json.dumps(filtered_publications, indent=4), f, indent=4)
