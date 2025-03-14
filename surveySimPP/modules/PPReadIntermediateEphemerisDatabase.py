#!/usr/bin/python

import pandas as pd
import sqlite3
import logging
import sys

# Author: Grigori fedorets


def PPReadIntermediateEphemerisDatabase(intermdb, part_objid_list):
    """
    PPReadIntermediateEphemerisDatabase.py

    Description: This task reads in the intermediate pointing sqlite3 database specified
    by a subset of object ids, and outputs a pandas dataframe.

    Mandatory input:      string, intermdb, name of intermediate database sqlite3 database
                          list(string), list of input ObjIDs

    Output:               pandas dataframe

    usage: padafr=PPReadIntermDatabase(intermdb,part_objid_list)
    """

    pplogger = logging.getLogger(__name__)

    con = sqlite3.connect(intermdb)
    cursor1 = con.execute('select * from interm')
    namespd = list(map(lambda x: x[0], cursor1.description))

    part_objid_list_ = tuple(part_objid_list)
    part_objid_list_ = [(i,) for i in part_objid_list]

    cur = con.cursor()

    padafr = []
    for j in part_objid_list_:
        cur.execute("SELECT * from interm WHERE ObjID IN (?);", j)
        padafrtmp = pd.DataFrame(cur.fetchall(), columns=namespd)
        padafr.append(padafrtmp)
    padafr = pd.concat(padafr)

    padafr = padafr.drop(['V', 'V(H=0)'], axis=1, errors='ignore')

    try:
        padafr['ObjID'] = padafr['ObjID'].astype(str)
    except KeyError:
        pplogger.error("ERROR: ephemeris input file does not have 'ObjID' column.")
        sys.exit("ERROR: ephemeris input file does not have 'ObjID' column.")

    return padafr
