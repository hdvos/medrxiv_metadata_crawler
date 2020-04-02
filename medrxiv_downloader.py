"""Crawls https://www.medrxiv.org/ for metadata given search terms.

usage: python medrxiv_downloader.py -i search_terms.txt -o output.csv

Takes a text file as input (-i) and a csv file as output. 
Input file is a text file that contains 1 search term per line.
Output file is a csv file (tabs separated (\t)). All data will be written to this file.

Author: Hugo de Vos
Last alteration by Hugo de Vos: April 2, 2020
On the date of last alteration all code was complient with the robots.txt at that time. (https://www.medrxiv.org/robots.txt)


"""
import argparse
from csv import DictWriter
from bs4 import BeautifulSoup
from datetime import datetime
import re
import requests
from urllib.parse import urljoin

DEBUG = False

parser = argparse.ArgumentParser(description='Input and output files.')
parser.add_argument('-i', type=str, dest='input_filename',
    help='A file with on every line a search term')
parser.add_argument('-o', type=str, dest='output_filename',
    help='Where the output will be written')

args = parser.parse_args()

base_url = "https://www.medrxiv.org/"

data = []

def write(some_data):
    print("\tSaving ...")
    with open(args.output_filename, 'wt') as csvfile:
        fieldnames = ['title', 'authors', 'date', 'data_availability', 'search term', 'doi', 'url','abstract']
        writer = DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')

        writer.writeheader()
        for item in data:
            writer.writerow(item)


def read_input_file(filename:str) -> list:
    with open(filename, 'rt') as f:
        terms = f.readlines()
    terms = [term.strip() for term in terms]
    terms = [term.replace(' ', '%252B') for term in terms]
    return terms

def make_url(search_term:str, i:int, results_per_page:int = 10) -> str:
    return f"https://www.medrxiv.org/search/{search_term} numresults%3A{results_per_page} sort%3Apublication-date direction%3Adescending?page={i}"

def check_status_code(response:requests.models.Response, url:str):
    if not response.status_code == 200:
        raise RuntimeError(f"Unable to retrieve page {url}.\nStatus Code: {response.status_code}")

def make_article_urls(href):
    abstract_url = urljoin(base_url, href)

    return abstract_url

def process_names(names_soup_list):
    names_soup = names_soup_list[0]
    names_string = names_soup.text
    names_list = names_string.split(',')
    names_list = [name.strip() for name in names_list]

    return names_list

def process_text(text:str) -> str:
    text = ' '.join(text.splitlines())
    text = re.sub(r"{[^}]+}", " ", text)
    re.sub(r"<[^>]+>", ' ', text)
    text = text.replace("}(document, 'script', 'twitter-wjs');", " ")
    text = text.replace("lang: en_US Tweet !function(d,s,id)", ' ')
    
    text = re.sub(r' +', ' ', text)
    return text

def parse_availability(availability):
    availability = availability.lower()
    if 'confidential' in availability:
        return "confidential"
    elif "github" in availability:
        return "github"
    elif "gitlab" in availability:
        return "gitlab"
    elif "zenodo" in availability:
        return "zenodo"
    elif "request" in availability:
        return "upon request"

    return "other"
    

def process_article(summary_soup, data, term):
    #TODO: try except clause around url
    href = summary_soup.select('.highwire-cite-linked-title')[0]['href']
    abstract_url, metric_url = make_article_urls(href)

    try:
        names_soup_list = summary_soup.select(".highwire-citation-authors")
        names_list = process_names(names_soup_list)
        names_str = '; '.join(names_list).replace('\n',' ')
    except:
        names_str = "NULL"

    try:
        doi = summary_soup.select('.highwire-cite-metadata-doi')[0].text
        doi = doi.replace('doi:', '').strip()
    except:
        doi = "NULL"

    article_page_response = requests.get(abstract_url)
    try:
        check_status_code(article_page_response, abstract_url)
    except RuntimeError:
        item = {
            'title':"UNK",
            'authors':names_str,
            'date':"UNK",
            'data_availability':"UK",
            'search term':term,
            'doi':doi,
            'url':abstract_url,
            'abstract':"UNK"

        }
        data.append(item)
        return


    article_page_soup = BeautifulSoup(article_page_response.text, features= 'lxml')
    
    date_rough = article_page_soup.select('.pane-1 > div:nth-child(1)')[0].text.strip().replace('\xa0', ' ')
    date = datetime.strptime(date_rough, 'Posted %B %d, %Y.').strftime('%Y-%m-%d')
    

    title = article_page_soup.select('#page-title')[0].text.strip()
    print(f"\t\t-{title}")
    print(f"\t\t\t{date}")
    print(f"\t\t\t{names_str}")

    abstract = article_page_soup.select('#abstract-1')[0].text
    abstract = process_text(abstract)
    
    data_availability = article_page_soup.select("#sec-1")[0].text
    availability_class = parse_availability(data_availability)
    # TODO parse data availability
    print(metric_url)
    

    item = {
        'title':title,
        'authors':names_str,
        'date':date,
        'data_availability':availability_class,
        'search term':term,
        'doi':doi,
        'url':abstract_url,
        'abstract':abstract

    }
    data.append(item)

def get_data_for_term(term:str, data:list):
    go_on = True
    i = 0
    while go_on:
        print(f"\tProcessing page {i + 1}")
        results_page_url = make_url(term, i)
        response = requests.get(results_page_url)
        check_status_code(response, results_page_url)

        results_page_soup = BeautifulSoup(response.text, features='lxml')

        result_summaries = results_page_soup.select(".highwire-article-citation")

        for summary_soup in result_summaries:
            process_article(summary_soup, data, term)
            if DEBUG: input()

        write(data)
        
        
        i += 1


        if i == 10 and DEBUG:
            break

if __name__ == "__main__":
    search_terms = read_input_file(args.input_filename)

    for search_term in search_terms:
        print(f"Get data for term {search_term}")
        get_data_for_term(search_term, data)

    print(search_terms)
