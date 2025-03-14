import logging
import sys
import numpy as np

# Author: Steph Merritt


def PPApplyColourOffsets(observations, function, othercolours, observing_filters, mainfilter):
    """Adds the correct colour offset to H based on the filter of each observation,
    then checks to make sure the appropriate columns exist for each phase function model.
    If phase model variables exist for each colour, this function also selects the
    correct variables for each observation based on filter.

    parameters:
    -------------
    observations (Pandas dataframe): pandas dataframe of observations
    function (string): string of desired phase function model
    othercolours (list of strings): list of colour offsets present in input files
    observing_filters (list of strings): list of observing filters
    mainfilter (string): the main filter in which H is given and all colour offsets are calculated against

    """

    pplogger = logging.getLogger(__name__)

    # create a zero-offset column for mainfilter-mainfilter
    observations[mainfilter + "-" + mainfilter] = np.zeros(len(observations))

    # first apply the H offset for every observation
    try:
        observations["H"] = observations.apply(lambda row: row['H'] + row[row["optFilter"] + "-" + mainfilter], axis=1)
    except KeyError:
        pplogger.error('ERROR: PPApplyColourOffsets: H column missing!')
        sys.exist('ERROR: PPApplyColourOffsets: H column missing!')

    # then check the function
    # for each function, see if the basic columns exist: if so, leave them
    # if colour-specific terms exist, make columns with the appropriate values

    if function == 'HG1G2':
        G1list = ['G1' + filt for filt in observing_filters]
        G2list = ['G2' + filt for filt in observing_filters]
        col_list = ['H'] + G1list + G2list

        if set(['H', 'G1', 'G2']).issubset(observations.columns):
            pass
        elif set(col_list).issubset(observations.columns):
            observations["G1"] = observations.apply(lambda row: row["G1" + row["optFilter"]], axis=1)
            observations["G2"] = observations.apply(lambda row: row["G2" + row["optFilter"]], axis=1)
            observations.drop(col_list[1:], axis=1, inplace=True)
        else:
            pplogger.error('ERROR: PPApplyColourOffsets: HG1G2 function requires the following input data columns: H, G1, G2.')
            sys.exit('ERROR: PPApplyColourOffsets: HG1G2 function requires the following input data columns: H, G1, G2.')

    elif function == 'HG':
        Glist = ['GS' + filt for filt in observing_filters]
        col_list = ['H'] + Glist

        if set(['H', 'GS']).issubset(observations.columns):
            pass
        elif set(col_list).issubset(observations.columns):
            observations["GS"] = observations.apply(lambda row: row["GS" + row["optFilter"]], axis=1)
            observations.drop(col_list[1:], axis=1, inplace=True)
        else:
            pplogger.error('ERROR: PPApplyColourOffsets: HG function requires the following input data columns: H, GS.')
            sys.exit('ERROR: PPApplyColourOffsets: HG function requires the following input data columns: H, GS.')

    elif function == 'HG12':
        G12list = ['G12' + filt for filt in observing_filters]
        col_list = ['H'] + G12list

        if set(['H', 'G12']).issubset(observations.columns):
            pass
        elif set(col_list).issubset(observations.columns):
            observations["G12"] = observations.apply(lambda row: row["G12" + row["optFilter"]], axis=1)
            observations.drop(col_list[1:], axis=1, inplace=True)
        else:
            pplogger.error('ERROR: PPApplyColourOffsets: HG12 function requires the following input data columns: H, G12.')
            sys.exit('ERROR: PPApplyColourOffsets: HG12 function requires the following input data columns: H, G12.')

    elif function == 'linear':
        Slist = ['S' + filt for filt in observing_filters]
        col_list = ['H'] + Slist

        if set(['H', 'S']).issubset(observations.columns):
            pass
        elif set(col_list).issubset(observations.columns):
            observations["S"] = observations.apply(lambda row: row["S" + row["optFilter"]], axis=1)
            observations.drop(col_list[1:], axis=1, inplace=True)
        else:
            pplogger.error('ERROR: PPApplyColourOffsets: linear function requires the following input data columns: H, S.')
            sys.exit('ERROR: PPApplyColourOffsets: linear function requires the following input data columns: H, S.')

    elif function == 'H':
        pass

    else:
        pplogger.error('ERROR: PPApplyColourOffsets: unknown phase function. Should be HG1G2, HG, HG12 or linear.')
        sys.exit('ERROR: PPApplyColourOffsets: unknown phase function. Should be HG1G2, HG, HG12 or linear.')

    # drop a few more unneeded columns to reduce size of dataframe :)
    observations.drop(mainfilter + "-" + mainfilter, axis=1, inplace=True)
    observations.drop(othercolours, axis=1, inplace=True)

    return observations
