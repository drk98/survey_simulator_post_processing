# Developed for the Vera C. Rubin Observatory/LSST Data Management System.
# This product includes software developed by the
# Vera C. Rubin Observatory/LSST Project (https://www.lsst.org).
#
# Copyright 2020 University of Washington
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Calculate probability of detection due to fading

"""

import numpy as np
import sys
import logging

__all__ = ['PPDetectionProbability']


############################################
# MODULE SPECIFIC EXCEPTION
###########################################
class Error(Exception):
    """Vector module specific exception."""

    pass

# -----------------------------------------------------------------------------------------------


def calcDetectionProbability(mag, limmag, fillFactor=1.0, w=0.1):
    """ Find the probability of a detection given a visual magnitude,
    limiting magnitude, and fillfactor,
    determined by the fading function from Veres & Chesley (2017).

    Parameters
    ----------
    mag: float
            magnitude of object in filter used for that field
    limmag: float
         limiting magnitude of the field
    fillfactor: float
         fraction of FOV covered by the camera sensor
    w: float
         distribution parameter

    Returns
    -------
    P: float
        Probability of detection
    """

    P = fillFactor / (1. + np.exp((mag - limmag) / w))

    return P

# -----------------------------------------------------------------------------------------------


def PPDetectionProbability(oif_df, trailing_losses=False, trailing_loss_name='dmagDetect',
                           magnitude_name="observedTrailedSourceMag",
                           limiting_magnitude_name="fiveSigmaDepthAtSource",
                           field_id_name="FieldID",
                           fillFactor=1.0, w=0.1):

    """
    Probability of observations being observable for objectInField output.

    Input
    -----
    oif_df          ... pandas dataframe containing simulation output joined to pointing.
    *_name          ... names of columns in oif_df
    fillFactor      ... fraction of the field of view covered by sensors.
    w               ... distribution parameter
    """

    if not trailing_losses:
        return calcDetectionProbability(oif_df[magnitude_name], oif_df[limiting_magnitude_name], fillFactor, w)
    elif trailing_losses:
        return calcDetectionProbability(oif_df[magnitude_name] + oif_df[trailing_loss_name], oif_df[limiting_magnitude_name], fillFactor, w)
    else:
        pplogger = logging.getLogger(__name__)
        pplogger.error('ERROR: PPDetectionProbability: trailing_losses should be True or False.')
        sys.exit('ERROR: PPDetectionProbability: trailing_losses should be True or False.')
