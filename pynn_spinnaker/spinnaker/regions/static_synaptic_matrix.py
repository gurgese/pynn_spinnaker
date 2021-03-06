# Import modules
import logging
import numpy as np

# Import classes
from synaptic_matrix import SynapticMatrix

logger = logging.getLogger("pynn_spinnaker")


# ------------------------------------------------------------------------------
# StaticSynapticMatrix
# ------------------------------------------------------------------------------
class StaticSynapticMatrix(SynapticMatrix):
    # Static synapses are stored in single 32-bit words with the weight
    # stored in the bits above index and delay
    WeightShift = SynapticMatrix.IndexBits + SynapticMatrix.DelayBits

    # How many bits should fixed point weights be converted into
    # **NOTE** weights are only 16-bit, but final words need to be 32-bit
    FixedPointWeightBits = 32

    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _get_num_row_words(self, num_synapses):
        return self.NumHeaderWords + num_synapses

    def _get_num_ext_words(self, num_sub_rows, sub_row_lengths,
                           sub_row_sections):
        # Number of synapses in all but 1st delay
        # slot and header for each extension row to total
        return (sub_row_sections[-1] - sub_row_sections[0]) +\
            (self.NumHeaderWords * (num_sub_rows - 1))

    def _write_synapses(self, dtcm_delay, weight_fixed, indices, destination):
        destination[:] = (indices
                          | (dtcm_delay << self.IndexBits)
                          | (weight_fixed << self.WeightShift))

    def _read_synapses(self, synapse_words, weight_to_float, dtype, synapses):
        raise NotImplementedError()