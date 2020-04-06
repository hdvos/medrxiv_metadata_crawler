# medrxiv_metadata_crawler
Crawls https://www.medrxiv.org/ for metadata given some search terms.


usage: python medrxiv_downloader.py -i search_terms.txt -o output.csv

Takes a text file as input (-i) and a csv file (-o) as output. 
Input file is a text file that contains 1 search term per line.
Output file is a csv file (tabs separated (\t)). All data will be written to this file.

Author: Hugo de Vos
Last alteration by Hugo de Vos: April 2, 2020
On the date of last alteration all code was complient with the robots.txt at that time. (https://www.medrxiv.org/robots.txt)
