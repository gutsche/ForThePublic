#!/urs/bin/env python
# -*- coding: utf-8 -*-

import sys, re, time, argparse, os
from urllib2 import Request, urlopen, URLError
from bs4 import BeautifulSoup, Comment
import logging
import logging.config
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import *

logger = logging.getLogger(__name__)
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s %(funcName)s:%(lineno)d: %(message)s'
        },
     },
     'handlers': {
         'default': {
             'level':'DEBUG',
             'formatter': 'standard',
             'class':'logging.StreamHandler',
             },
          },
          'loggers': {
              '': {
                  'handlers': ['default'],
                  'level': 'WARNING',
                  'formatter': 'standard',
                  'propagate': True
              }
          }
})

inspirehepapi='http://inspirehep.net/search?'
author_query='author:O.Gutsche.1 AND collection:citeable'

def inspire_get_number_of_records():
    """
        return number of records for author_query
    """

    print("Querying Inspire for number of records")


    url = inspirehepapi + 'of=xm&rg=1&ot=001&p=' + author_query.replace(' ', '+')
    request = Request(url)
    try:
        response = urlopen(request)
        result = response.read()
        soup = BeautifulSoup(result, "lxml")
    except URLError, error:
        print 'URL =', url
        print 'No result. Got an error code:', error
        quit()
    try:
        comments = soup.findAll(text=lambda text:isinstance(text, Comment))
        number_of_records = int(re.sub(r'\D', '', comments[0]))
    except IndexError:
        number_of_records = 0

    print("OLI's publication list has %i records" % number_of_records)

    return number_of_records

def write_file(filename,input_string):
    with open(filename,'w') as output_file:
        output_file.write(input_string)

def inspire_get_bibtex(number_of_records):
    """
        get BiBTeX of all records
    """

    print("Querying Inspire for OLI's publication list records in BiBTeX format")

    db = BibDatabase()

    nrecords = 250
    nsteps = int(number_of_records/nrecords) + 1
    for step in range(nsteps):
        jrec = step*nrecords+1
        url = inspirehepapi + 'of=hx&rg='+str(nrecords)+'&jrec='+str(jrec)+'&p=' + author_query.replace(' ', '+')
        request = Request(url)
        try:
            response = urlopen(request)
            BiBTeX = response.read()
        except URLError, error:
            print 'URL =', url
            print 'No result. Got an error code:', error
            quit()

        if 'No records' in BiBTeX:
            print "no records were found in SPIRES to match your search, please try again"
            print 'url:',url
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
    with open(filename,'w') as output_file:
        bibtex_str = bibtexparser.dumps(db,writer=writer)
        output_file.write(bibtex_str.encode('utf8'))
        print("Wrote %i records into filename '%s'" % (len(db.entries),filename))

def load_bibtex_file(filename,create=False):
    """
        Load BiBTeX file, create bib database and return database
    """

    if create == True:
        if os.path.isfile(filename) == False:
            print("File with filename '%s' does not exist, creating empty file" % filename)
            open(filename, 'a').close()

    with open(filename) as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    print("Loaded BiBTeX database from file '%s' with %i entries" % (filename,len(bib_database.entries)))
    return bib_database

def add_additional_records(db,filename):
    """
        load filename bibtex file of additional bibtex records not covered by complete Inspire query and add them to DB
    """

    additional_db = load_bibtex_file(filename)
    db.entries.extend(additional_db.entries)
    print("Added %i additional entries not covered by complete Inspire query from filename '%s'" % (len(additional_db.entries),filename))

def update(inspire_db,physics_db,computing_db,experiment_db,short_physics_db,short_computing_db,shortest_physics_db,shortest_computing_db):
    """

    update records in physics, computing and experiment BibTeX files with records from the inspire BibTeX file
    always use the record labels for comparisons

    """
    new_keys = inspire_db.entries_dict.keys()
    physics_keys = physics_db.entries_dict.keys()
    computing_keys = computing_db.entries_dict.keys()
    experiment_keys = experiment_db.entries_dict.keys()
    short_physics_keys = short_physics_db.entries_dict.keys()
    short_computing_keys = short_computing_db.entries_dict.keys()
    shortest_physics_keys = shortest_physics_db.entries_dict.keys()
    shortest_computing_keys = shortest_computing_db.entries_dict.keys()
    missing_keys = []

    go_quit = False

    # which entries from physics_db have been deleted
    for key in physics_keys:
        if key not in new_keys:
            print("Physics DB entry '%s' was deleted from inspire, remove manually" % key)
            go_quit = True

    # which entries from computing_db have been deleted
    for key in computing_keys:
        if key not in new_keys:
            print("Computing DB entry '%s' was deleted from inspire, remove manually" % key)
            go_quit = True

    # which entries from experiment_db have been deleted
    for key in experiment_keys:
        if key not in new_keys:
            print("Experiment DB entry '%s' was deleted from inspire, remove manually" % key)
            go_quit = True

    # which keys are new
    for key in new_keys:
        if key not in physics_keys and key not in computing_keys and key not in experiment_keys:
            missing_keys.append(key)

    # check for missing keys and print them
    if len(missing_keys) > 0:
        print("Following records are new: '%s'" % '\',\''.join(missing_keys))

    #  move keys to physics or computing
    new_physics_keys = []
    new_computing_keys=[]
    physics_keys.extend(new_physics_keys)
    computing_keys.extend(new_computing_keys)
    # remove new keys from experiment
    for key in new_physics_keys:
        while key in experiment_keys:
            experiment_keys.remove(key)
    for key in new_computing_keys:
        while key in experiment_keys:
            experiment_keys.remove(key)

    # add new keys to experiment
    new_experiment_keys=[]
    experiment_keys.extend(new_experiment_keys)

    # update all keys in physics_db
    tmp_list = []
    for key in physics_keys:
        if key in new_keys:
            tmp_list.append(inspire_db.entries_dict[key])
    physics_db.entries = tmp_list

    # update all keys in computing_db
    tmp_list = []
    for key in computing_keys:
        if key in new_keys:
            tmp_list.append(inspire_db.entries_dict[key])
    computing_db.entries = tmp_list

    # update all keys in experiment_db
    tmp_list = []
    for key in experiment_keys:
        if key in new_keys:
            tmp_list.append(inspire_db.entries_dict[key])
    experiment_db.entries = tmp_list

    # update all keys in short_physics_db
    tmp_list = []
    for key in short_physics_keys:
        if key in new_keys:
            tmp_list.append(inspire_db.entries_dict[key])
    short_physics_db.entries = tmp_list

    # update all keys in short_computing_db
    tmp_list = []
    for key in short_computing_keys:
        if key in new_keys:
            tmp_list.append(inspire_db.entries_dict[key])
    short_computing_db.entries = tmp_list

    # update all keys in shortest_physics_db
    tmp_list = []
    for key in shortest_physics_keys:
        if key in new_keys:
            tmp_list.append(inspire_db.entries_dict[key])
    shortest_physics_db.entries = tmp_list

    # update all keys in shortest_computing_db
    tmp_list = []
    for key in shortest_computing_keys:
        if key in new_keys:
            tmp_list.append(inspire_db.entries_dict[key])
    shortest_computing_db.entries = tmp_list

    # consistency check
    if len(inspire_db.entries) != len(physics_db.entries)+len(computing_db.entries)+len(experiment_db.entries):
        print("Inconsistency: physics %i + computing %i + experiment %i = sum %i is not the same as inspire %i" % (len(physics_db.entries),len(computing_db.entries),len(experiment_db.entries),len(physics_db.entries)+len(computing_db.entries)+len(experiment_db.entries),len(inspire_db.entries)))
        go_quit = True

    return go_quit

def main(args):
    """

    generate publication list for O.Gutsche

    Use Inspire query

    http://inspirehep.net/search?author:O.Gutsche.1 AND collection:citeable

    and add additional records not covered by the query or read in BiBTeX file with the result of the query+additional records

    Then distribute the publication list into three BiBTeX files:

    1. physics: all physics publications with direct involvment from OLI
    2. computing: all computing publications with direct involvement from OLI
    3. experiment: all publications through membership in experiment collaborations without direct involvement from OLI

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="Increase verbosity of program output")
    parser.add_argument("--input", action="store", default = None, help="Specify filename of complete Inspire records query in BibTeX format instead of querying Inspire.")
    parser.add_argument("--additional", action="store", default = "additional_publication_list.bib", help="Filename of BiBTeX file with records in addition to a complete Inspire query")
    parser.add_argument("--output", action="store", default = "complete_publication_list.bib", help="Output file name to store all records of complete Inspire query")
    parser.add_argument("--physics", action="store", default = "physics_publication_list.bib", help="Filename of physics publications with direct involvement")
    parser.add_argument("--computing", action="store", default = "computing_publication_list.bib", help="Filename of computing publications with direct involvement")
    parser.add_argument("--experiment", action="store", default = "experiment_publication_list.bib", help="Filename of publications through membership in experiment collaborations")
    parser.add_argument("--short_physics", action="store", default = "short_physics_publication_list.bib", help="Filename of short physics publications with direct involvement")
    parser.add_argument("--short_computing", action="store", default = "short_computing_publication_list.bib", help="Filename of short computing publications with direct involvement")
    parser.add_argument("--shortest_physics", action="store", default = "shortest_physics_publication_list.bib", help="Filename of shortest physics publications with direct involvement")
    parser.add_argument("--shortest_computing", action="store", default = "shortest_computing_publication_list.bib", help="Filename of shortest computing publications with direct involvement")
    args = parser.parse_args()

    # how many entries are already tracked locally
    physics_db = load_bibtex_file(args.physics, True)
    computing_db = load_bibtex_file(args.computing, True)
    experiment_db = load_bibtex_file(args.experiment, True)
    short_computing_db = load_bibtex_file(args.short_computing, True)
    short_physics_db = load_bibtex_file(args.short_physics, True)
    shortest_computing_db = load_bibtex_file(args.shortest_computing, True)
    shortest_physics_db = load_bibtex_file(args.shortest_physics, True)
    print ("Locally tracking %i entries." % (len(physics_db.entries)+len(computing_db.entries)+len(experiment_db.entries)) )

    if args.input == None:
        number_of_records = inspire_get_number_of_records()
        inspire_db = inspire_get_bibtex(number_of_records)
        add_additional_records(inspire_db,args.additional)
    else:
        inspire_db = load_bibtex_file(args.input)

    go_quit = update(inspire_db,physics_db,computing_db,experiment_db,short_physics_db,short_computing_db,shortest_physics_db,shortest_computing_db)

    # not optional, always write the output files
    write_bibtex_file(args.output,inspire_db)

    if go_quit == True:
        print('Exiting before writing physics, computing and experiment bib files because of inconsistencies')
        quit()

    write_bibtex_file(args.physics,physics_db)
    write_bibtex_file(args.computing,computing_db)
    write_bibtex_file(args.experiment,experiment_db)
    write_bibtex_file(args.short_physics,short_physics_db)
    write_bibtex_file(args.short_computing,short_computing_db)
    write_bibtex_file(args.shortest_physics,shortest_physics_db)
    write_bibtex_file(args.shortest_computing,shortest_computing_db)

if __name__ == '__main__':
    main(sys.argv)
