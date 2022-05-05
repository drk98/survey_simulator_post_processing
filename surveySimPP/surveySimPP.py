#!/usr/bin/python

import sys
import time
import numpy as np
import argparse
from surveySimPP.modules import PPMatchPointing
from surveySimPP.modules import PPFilterSSPCriterionEfficiency
from surveySimPP.modules import PPTrailingLoss
from surveySimPP.modules import PPBrightLimit
from surveySimPP.modules import PPMakeIntermediatePointingDatabase
from surveySimPP.modules import PPCalculateApparentMagnitude
from surveySimPP.modules.PPApplyFOVFilter import PPApplyFOVFilter
from surveySimPP.modules.PPSNRLimit import PPSNRLimit
from surveySimPP.modules import PPAddUncertainties, PPRandomizeMeasurements
from surveySimPP.modules import PPVignetting
from surveySimPP.modules.PPFilterFadingFunction import PPFilterFadingFunction
from surveySimPP.modules.PPRunUtilities import PPGetLogger, PPConfigFileParser, PPPrintConfigsToLog, PPCMDLineParser, PPWriteOutput, PPReadAllInput
from surveySimPP.modules.PPMagnitudeLimit import PPMagnitudeLimit
#from surveySimPP.modules.PPOutput import PPOutWriteCSV, PPOutWriteSqlite3, PPOutWriteHDF5


# Author: Samuel Cornwall, Siegfried Eggl, Grigori Fedorets, Steph Merritt, Meg Schwamb

def runLSSTPostProcessing(cmd_args):

    """
    Runs the post processing survey simulator functions that apply a series of
    filters to bias a model Solar System smallbody population to what the
    Vera C. Rubin Observatory Legacy Survey of Space and Time would observe.

    Output:               csv, hdf5, or sqlite file
    """

    # Initialise argument parser and assign command line arguments

    pplogger = PPGetLogger()

    # Read, assign and error-handle the configuration file
    pplogger.info('Reading configuration file...')

    configs = PPConfigFileParser(cmd_args['configfile'], cmd_args['surveyname'])

    pplogger.info('Configuration file successfully read.')

    PPPrintConfigsToLog(configs)

    # End of config parsing

    if cmd_args['makeIntermediatePointingDatabase']:
        PPMakeIntermediatePointingDatabase.PPMakeIntermediatePointingDatabase(
                                cmd_args['oifoutput'],
                                './data/interm.db',
                                100)

    pplogger.info('Reading pointing database and matching observationID with appropriate optical filter...')
    filterpointing = PPMatchPointing.PPMatchPointing(
                                configs['pointingdatabase'],
                                configs['observing_filters'],
                                configs['ppdbquery'])

    pplogger.info('Instantiating random number generator ... ')
    rng_seed = int(time.time())
    pplogger.info('Random number seed is {}.'.format(rng_seed))
    rng = np.random.default_rng(rng_seed)

    # Extracting mainfilter, the first in observing_filters
    mainfilter = configs['observing_filters'][0]

    # In case of a large input file, the data is read in chunks. The
    # "sizeSerialChunk" parameter in PPConfig.ini assigns the chunk.

    # Here, add loop which reads only a portion of input file to
    # avoid memory overflow
    startChunk = 0
    endChunk = 0
    # number of rows in an entire orbit file

    ii = -1
    with open(cmd_args['orbinfile']) as f:
        for ii, l in enumerate(f):
            pass
    lenf = ii

    while(endChunk < lenf):
        endChunk = startChunk + configs['sizeSerialChunk']
        if (lenf-startChunk > configs['sizeSerialChunk']):
            incrStep = configs['sizeSerialChunk']
        else:
            incrStep = lenf-startChunk

        # Processing begins, all processing is done for chunks

        observations = PPReadAllInput(cmd_args, configs, filterpointing,
                                      startChunk, incrStep)

        pplogger.info('Calculating apparent magnitudes...')
        observations = PPCalculateApparentMagnitude.PPCalculateApparentMagnitude(
            observations, configs['phasefunction'], mainfilter,
            configs['othercolours'], configs['observing_filters'],
            configs['objecttype'])

        #----------------------------------------------------------------------
        if configs['trailingLossesOn']:
            pplogger.info('Calculating trailing losses...')
            dmagDetect = PPTrailingLoss.PPTrailingLoss(observations, "circularPSF")
            observations['PSFMag'] = dmagDetect + observations['TrailedSourceMag']
        else:
            observations['PSFMag'] = observations['TrailedSourceMag']
        #----------------------------------------------------------------        

        pplogger.info('Calculating effects of vignetting on limiting magnitude...')
        observations['fiveSigmaDepthAtSource'] = PPVignetting.vignettingEffects(observations)

        pplogger.info('Calculating astrometric and photometric uncertainties...')
        observations = PPAddUncertainties.addUncertainties(observations, rng)

        pplogger.info('Dropping observations with signal to noise ratio less than {}...'.format(configs['SNRLimit']))
        observations = PPSNRLimit(observations, configs['SNRLimit'])
        
        if configs['brightLimit']:
            pplogger.info('Dropping observations that are too bright...')
            observations = PPBrightLimit.PPBrightLimit(
                observations,
                configs['brightLimit'])

        pplogger.info('Applying field-of-view filters...')
        observations = PPApplyFOVFilter(observations, configs)

        if configs['magLimit']:
            pplogger.info('Dropping detections fainter than user-defined magnitude limit... ')
            observations = PPMagnitudeLimit(observations, configs['magLimit'])

        pplogger.info('Applying astrometric uncertainties...')
        observations["AstRATrue(deg)"] = observations["AstRA(deg)"]
        observations["AstDecTrue(deg)"] = observations["AstDec(deg)"]
        observations["AstRA(deg)"], observations["AstDec(deg)"] = PPRandomizeMeasurements.randomizeAstrometry(observations, rng, sigName='AstrometricSigma(deg)')

        pplogger.info('Applying fading function...')
        observations = PPFilterFadingFunction(observations, configs['fillfactor'], rng)

        if configs['SSPFiltering']:
            pplogger.info('Applying SSP criterion efficiency...')

            observations = PPFilterSSPCriterionEfficiency.PPFilterSSPCriterionEfficiency(
                        observations, configs['SSPDetectionEfficiency'],
                        configs['minTracklet'], configs['noTracklets'],
                        configs['trackletInterval'], configs['inSepThreshold'],
                        rng)

            observations = observations.drop(['index'], axis='columns')
            observations.reset_index(drop=True, inplace=True)
            pplogger.info('Number of rows AFTER applying SSP criterion threshold: ' + str(len(observations.index)))

        # write output
        PPWriteOutput(configs, observations, endChunk)

        startChunk = startChunk + configs['sizeSerialChunk']
        # end for

    pplogger.info('Post processing completed.')


def main():
    """

    A post processing survey simulator that applies a series of filters to bias a model Solar System small body population to what the specified wide-field survey would observe.

    Mandatory input:      configuration file, orbit file, physical parameters file, and optional cometary activity properties file

    Output:               csv, hdf5, or sqlite file


    usage: surveySimPP [-h] [-c C] [-d] [-m M] [-l L] [-o O] [-p P] [-s S]
        optional arguments:
         -h, --help      show this help message and exit
         -c C, --config C   Input configuration file name
         -d          Make intermediate pointing database
         -m M, --comet M    Comet parameter file name
         -l L, --params L   Physical parameters file name
         -o O, --orbit O    Orbit file name
         -p P, --pointing P  Pointing simulation output file name
         -s S, --survey S   Name of the survey you wish to simulate
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Input configuration file name", type=str, dest='c', default='./PPConfig.ini', required=True)
    parser.add_argument("-d", help="Make intermediate pointing database", dest='d', action='store_true')
    parser.add_argument("-m", "--comet", help="Comet parameter file name", type=str, dest='m')
    parser.add_argument("-l", "--params", help="Physical parameters file name", type=str, dest='l', default='./data/params', required=True)
    parser.add_argument("-o", "--orbit", help="Orbit file name", type=str, dest='o', default='./data/orbit.des', required=True)
    parser.add_argument("-p", "--pointing", help="Pointing simulation output file name", type=str, dest='p', default='./data/oiftestoutput', required=True)
    parser.add_argument("-s", "--survey", help="Survey to simulate", type=str, dest='s', default='LSST')

    cmd_args = PPCMDLineParser(parser)

    if cmd_args['surveyname'] in ['LSST', 'lsst']:
        runLSSTPostProcessing(cmd_args)
    else:
        sys.exit('ERROR: Survey name not recognised. Current allowed surveys are: {}'.format(['LSST', 'lsst']))


if __name__ == '__main__':
    main()
