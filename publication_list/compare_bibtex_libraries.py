#!/usr/bin/env python3
import sys, os, re, json
from urllib.request import Request, urlopen
from urllib.error import URLError

import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import *

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

def create_key_mapping_dict(db):
    output = {}
    for key in db.entries_dict.keys():
        tmp = {}
        found_one = False
        if "eprint" in db.entries_dict[key].keys(): 
                tmp["eprint"] = db.entries_dict[key]["eprint"]
                found_one = True
        if "doi" in db.entries_dict[key].keys(): 
                tmp["doi"] = db.entries_dict[key]["doi"]
                found_one = True
        if "reportnumber" in db.entries_dict[key].keys(): 
                tmp["reportnumber"] = db.entries_dict[key]["reportnumber"]
                found_one = True
        if found_one == False:
            print(db.entries_dict[key])
        output[key] = tmp
    return output

def match_entries(old_entries,new_entries):
    matches = {}
    for old_key in old_entries.keys():
        matches[old_key] = False
    for new_key in new_entries.keys():
        for old_key in old_entries.keys():
            for check_key in old_entries[old_key].keys():
                if check_key in new_entries[new_key].keys():
                    if old_entries[old_key][check_key] == new_entries[new_key][check_key]:
                        matches[old_key] = new_key
                        break    
    
    for key in matches:
        if matches[key] == False:
            print("match failed for old_key: {}".format(key))
    return matches

def main(args):
    org_complete_db = load_bibtex_file("complete_publication_list.bib")
    org_computing_db = load_bibtex_file("computing_publication_list.bib")
    org_physics_db = load_bibtex_file("physics_publication_list.bib")
    org_short_computing_db = load_bibtex_file("short_computing_publication_list.bib")
    org_short_physics_db = load_bibtex_file("short_physics_publication_list.bib")
    org_shortest_computing_db = load_bibtex_file("shortest_computing_publication_list.bib")
    org_shortest_physics_db = load_bibtex_file("shortest_physics_publication_list.bib")

    org_complete_mapping = create_key_mapping_dict(org_complete_db)
    org_computing_mapping = create_key_mapping_dict(org_computing_db)
    org_physics_mapping = create_key_mapping_dict(org_physics_db)
    org_short_computing_mapping = create_key_mapping_dict(org_short_computing_db)
    org_short_physics_mapping = create_key_mapping_dict(org_short_physics_db)
    org_shortest_computing_mapping = create_key_mapping_dict(org_shortest_computing_db)
    org_shortest_physics_mapping = create_key_mapping_dict(org_shortest_physics_db)

    org_computing_ids = match_entries(org_computing_mapping,org_complete_mapping)
    org_physics_ids = match_entries(org_physics_mapping,org_complete_mapping)
    org_short_computing_ids = match_entries(org_short_computing_mapping,org_complete_mapping)
    org_short_physics_ids = match_entries(org_short_physics_mapping,org_complete_mapping)
    org_shortest_computing_ids = match_entries(org_shortest_computing_mapping,org_complete_mapping)
    org_shortest_physics_ids = match_entries(org_shortest_physics_mapping,org_complete_mapping)

    new_experiment_db = BibDatabase()
    new_computing_db = BibDatabase()
    new_physics_db = BibDatabase()
    new_short_computing_db = BibDatabase()
    new_short_physics_db = BibDatabase()
    new_shortest_computing_db = BibDatabase()
    new_shortest_physics_db = BibDatabase()

    for entry in org_complete_db.entries:
        if entry['ID'] in list(org_computing_ids.values()):
            new_computing_db.entries.append(entry)
        elif entry['ID'] in list(org_physics_ids.values()):
            new_physics_db.entries.append(entry)
        else:
            new_experiment_db.entries.append(entry)
    
    for old_id in org_short_computing_ids:
        new_short_computing_db.entries.append(org_complete_db.entries_dict[org_short_computing_ids[old_id]])
    for old_id in org_short_physics_ids:
        new_short_physics_db.entries.append(org_complete_db.entries_dict[org_short_physics_ids[old_id]])
    for old_id in org_shortest_computing_ids:
        new_shortest_computing_db.entries.append(org_complete_db.entries_dict[org_shortest_computing_ids[old_id]])
    for old_id in org_shortest_physics_ids:
        new_shortest_physics_db.entries.append(org_complete_db.entries_dict[org_shortest_physics_ids[old_id]])

    write_bibtex_file("new_experiment_publication_list.bib",new_experiment_db)
    write_bibtex_file("new_computing_publication_list.bib",new_computing_db)
    write_bibtex_file("new_physics_publication_list.bib",new_physics_db)
    write_bibtex_file("new_short_computing_publication_list.bib",new_short_computing_db)
    write_bibtex_file("new_short_physics_publication_list.bib",new_short_physics_db)
    write_bibtex_file("new_shortest_computing_publication_list.bib",new_shortest_computing_db)
    write_bibtex_file("new_shortest_physics_publication_list.bib",new_shortest_physics_db)

if __name__ == '__main__':
    main(sys.argv)