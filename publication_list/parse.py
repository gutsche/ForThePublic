#!/usr/bin/env python3
import sys, os, re, json
from urllib.request import Request, urlopen
from urllib.error import URLError

import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import *

inspirehepapi='https://inspirehep.net/api/literature?'
author_query='q=author%3AO.Gutsche.1%20AND%20collection%3Aciteable'

def inspire_get_number_of_records():
    """
        return number of records for author_query
    """

    print("Querying Inspire for number of records")


    # url = inspirehepapi + 'sort=mostrecent&size=25&page=1&' + author_query
    # request = Request(url)
    # number_of_records = 0
    # try:
    #     response = urlopen(request)
    #     result = json.loads(response.read())
    # except URLError as error:
    #     print('URL = {}'.format(url))
    #     print('No result. Got an error code: {}'.format(error))
    #     quit()
    # number_of_records = result['hits']['total']
    number_of_records = 1181
    
    print("OLI's publication list has %i records" % number_of_records)

    return number_of_records

def inspire_get_bibtex(number_of_records):
    """
        get BiBTeX of all records
    """

    # https://inspirehep.net/api/literature\?sort\=mostrecent\&size\=25\&page\=2\&q\=author%3AO.Gutsche.1%20AND%20collection%3Aciteable\&format\=bibtex
    print("Querying Inspire for OLI's publication list records in BiBTeX format")

    db = BibDatabase()

    nrecords = 25
    npages = int(number_of_records/nrecords) + 1
    for page in range(npages):
        page+=1
        print('Querying for page {} of {} pages.'.format(int(page),int(npages)))
        url = inspirehepapi + 'sort=mostrecent&size='+str(nrecords)+'&page='+str(page)+'&format=bibtex&' + author_query
        request = Request(url)
        try:
            response = urlopen(request)
            BiBTeX = response.read()
        except URLError as error:
            print('URL = {}'.format(url))
            print('No result. Got an error code: {}'.format(error))
            quit()

        if 'No records' in BiBTeX.decode('utf-8'):
            print('no records were found in SPIRES to match your search, please try again')
            print('url: {}'.format(url))
            quit()

        parser = BibTexParser()
        tmp_db = bibtexparser.loads(BiBTeX, parser=parser)
        for entry in tmp_db.entries:
            # repair some broken output
            entry['title'] = entry['title'].replace('\n',' ')
            entry['title'] = entry['title'].replace('\sqrts','\sqrt{s}')
            entry['title'] = entry['title'].replace(' $','$')
            entry['title'] = entry['title'].replace('amp;','')
            entry['title'] = entry['title'].replace('text {','text{')
            entry['title'] = re.sub(r"\\text\{(.*?)\}",r"\\mathrm{\1}",entry['title'])
            entry['title'] = re.sub(r"([^ ])\$",r"\1 $",entry['title'])
            entry['title'] = entry['title'].replace('\\,\\mathrm','\\mathrm')
            entry['title'] = entry['title'].replace('\\;\\mathrm','\\mathrm')
            entry['title'] = entry['title'].replace('=\\ ','=')
            entry['title'] = entry['title'].replace('\\mathrm {','\\mathrm{')
            entry['title'] = entry['title'].replace('_\mathrm{NN}','_{\\mathrm{NN}}')
            entry['title'] = entry['title'].replace('$\sigma_\mathrm{t \\bar{t} b \\bar{b}} / \sigma_\mathrm{t \\bar{t}  jj } $','$\sigma_{\mathrm{t \\bar{t} b \\bar{b}}} / \sigma_{\mathrm{t \\bar{t}  jj }} $')
            entry['title'] = entry['title'].replace('$13','$ 13')
            entry['title'] = entry['title'].replace('$8','$ 8')
            entry['title'] = entry['title'].replace('\mathrm','')
            entry['title'] = entry['title'].replace('\mathit','')
            if 'doi' in entry.keys(): entry['doi'] = entry['doi'].split(',')[0].strip()

            if 'eprint' in entry.keys():
                eprint = entry['eprint']
                prefix = 'arXiv'
                if 'archiveprefix' in entry.keys(): prefix = entry['archiveprefix']
                primaryclass = 'hep-ex'
                if 'primaryclass' in entry.keys(): primaryclass = entry['primaryclass']
                url = 'http://arxiv.org/abs/' + eprint
                urltext = eprint + ' [' + primaryclass +']'
                note = prefix + ':\\href{' + url + '}{' + urltext + '}'
                entry['note'] = note

        db.entries.extend(tmp_db.entries)
    print("OLI's publication db has: %i entries" % len(db.entries))
    return db

def write_bibtex_file(filename,db):
    """
        Write BiBTeX file with content from db
    """

    writer = BibTexWriter()
    writer.order_entries_by = ('year','ID')
    with open(filename,'wb') as output_file:
        bibtex_str = bibtexparser.dumps(db,writer=writer)
        output_file.write(bibtex_str.encode('utf8'))
        print("Wrote %i records into filename '%s'" % (len(db.entries),filename))

def main(args):
    number_of_records = inspire_get_number_of_records()
    inspire_db = inspire_get_bibtex(number_of_records)
    # not optional, always write the output files
    write_bibtex_file("test.bib",inspire_db)

if __name__ == '__main__':
    main(sys.argv)