#!/usr/bin/python
import sqlite3
import pandas as pd
import logging
import sys

# Author: Grigori Fedorets


def PPMatchPointing(bsdbname, observing_filters, dbquery):

    """
    PPMatchPointing.py



    Description: This task reads in the main baseline database, and extracts observationID,
    observationsStartMJD, used filter and three seeing parameters at a given pointing and outputs a 6*n pandas dataframe.


    Mandatory input:      bsdbname:   string, name of database
                          observing_filters: array of strings, filters required for output
                          dbquery:    string, SQLite3 query for querying the pointing database (defined in configuration file)

    Output:               8*n pandas dataframe


    usage: padafr=PPMatchPointing(bsdbname,observing_filters,dbquery)
    """

    pplogger = logging.getLogger(__name__)

    con = sqlite3.connect(bsdbname)

    try:
        df = pd.read_sql_query(dbquery, con)
    except Exception:
        pplogger.error('ERROR: PPMatchPointing: SQL query on pointing database failed. Check that the query is correct in the config file.')
        sys.exit('ERROR: PPMatchPointing: SQL query on pointing database failed. Check that the query is correct in the config file.')

    # df = pd.read_sql_query('SELECT observationId, observationStartMJD, filter, seeingFwhmGeom, seeingFwhmEff, fiveSigmaDepth, fieldRA, fieldDec, rotSkyPos FROM SummaryAllProps order by observationId', con)
    df['observationId_'] = df['observationId']
    df = df.rename(columns={'observationId': 'FieldID'})
    df = df.rename(columns={'observationId': 'FieldID'})
    df = df.rename(columns={'filter': 'optFilter'})  # not to confuse with the pandas filter command
    dfo = df[df.optFilter.isin(observing_filters)]

    return dfo
