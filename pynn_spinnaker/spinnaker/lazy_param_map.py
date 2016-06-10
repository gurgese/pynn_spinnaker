# Import modules
import lazyarray as la
import logging
import numpy as np
import sentinel

# Import classes
from utils import LazyArrayFloatToFixConverter

# Import functions
from copy import deepcopy
from functools import partial
from six import callable

logger = logging.getLogger("pynn_spinnaker")

# Create a converter functions to convert from float to
# various fixed-point formats used by PyNN SpiNNaker
float_to_s1615_no_copy = LazyArrayFloatToFixConverter(True, 32, 15, False)
float_to_s2011_no_copy = LazyArrayFloatToFixConverter(True, 32, 11, False)
float_to_u032_no_copy = LazyArrayFloatToFixConverter(False, 32, 32, False)
float_to_s411_no_copy = LazyArrayFloatToFixConverter(True, 16, 11, False)

# Sentinel used to indicate that a constant field should be used for Indices
Indices = sentinel.create("Indices")

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------
def _build_dtype(param_map):
    # Build numpy record datatype for neuron region
    # **TODO** this probably doesn't need to be a string:
    # could use np.uint8 style things throughout
    return np.dtype(",".join(zip(*param_map)[1]))

def size(param_map, size):
    return _build_dtype(param_map).itemsize * size

def apply(lazy_params, param_map, size, **kwargs):
    # Build a numpy record array large enough for all neurons
    params = np.empty(size, dtype=_build_dtype(param_map))

    # Loop through parameters
    # **YUCK** if there is only a single parameter,
    # numpy won't bother assigning a name
    param_names = (params.dtype.names
                   if params.dtype.names is not None
                   else (slice(None, None, None),))
    for field_name, param in zip(param_names, param_map):
        # If this map entry has a constant value,
        if len(param) == 2:
            param_value, _ = param

            # If parameter value is a lazy array,
            # evaluate it and copy into field
            if isinstance(param_value, la.larray):
                params[field_name] = param_value.evaluate()
            # Otherwise, if parameter value is callable,
            # call it and evaluate the result
            elif callable(param_value):
                params[field_name] = param_value(**kwargs).evaluate()
            # Otherwise, assuming it's a scalar, copy it into all fields
            else:
                params[field_name][:] = param_value
        # Otherwise
        else:
            param_name, _, param_mapping = param

            # Set parameter size
            lazy_params[param_name].shape = (size,)

            # Apply lazy transformation and evaluate
            params[field_name] = param_mapping(lazy_params[param_name], **kwargs).evaluate()

    return params


def apply_indices(lazy_params, param_map, indices, **kwargs):
    # Build a numpy record array large enough for all neurons
    params = np.empty(len(indices), dtype=_build_dtype(param_map))

    # Loop through parameters
    for field_name, param in zip(params.dtype.names, param_map):
        # If this map entry has a constant value
        if len(param) == 2:
            param_value, _ = param

            # If parameter should be used for indices, copy them in
            if param_value is Indices:
                params[field_name] = indices
            # Otherwise, if parameter value is a lazy array,
            # evaluate it and copy into field
            elif isinstance(param_value, la.larray):
                params[field_name] = param_value.evaluate()
            # Otherwise, if parameter value is callable,
            # call it and evaluate the result
            elif callable(param_value):
                params[field_name] = param_value(**kwargs).evaluate()
            # Otherwise, assuming it's a scalar, copy it into all fields
            else:
                params[field_name][:] = param_value
        # Otherwise
        elif len(indices) > 0:
            param_name, _, param_mapping = param

            # Set parameter size
            if not hasattr(lazy_params[param_name].base_value, "shape"):
                lazy_params[param_name].shape = (max(indices) + 1,)

            # Apply lazy transformation and evaluate slice
            params[field_name] = param_mapping(lazy_params[param_name],
                                               **kwargs)[indices]

    return params


def integer(values, **kwargs):
    vals = deepcopy(values)
    return la.rint(vals)


def integer_time_divide(values, sim_timestep_ms, **kwargs):
    # Copy values and divide by timestep
    scaled_vals = deepcopy(values)
    scaled_vals /= sim_timestep_ms

    # Round and return
    return la.rint(scaled_vals)


def s1615(values, **kwargs):
    return float_to_s1615_no_copy(deepcopy(values))

def s2011(values, **kwargs):
    return float_to_s2011_no_copy(deepcopy(values))

def u32_weight_fixed_point(values, weight_fixed_point, **kwargs):
    float_to_weight_no_copy = LazyArrayFloatToFixConverter(
        False, 32, weight_fixed_point, False)
    return float_to_weight_no_copy(deepcopy(values))

def s32_weight_fixed_point(values, weight_fixed_point, **kwargs):
    float_to_weight_no_copy = LazyArrayFloatToFixConverter(
        True, 32, weight_fixed_point, False)
    return float_to_weight_no_copy(deepcopy(values))

def time_multiply(values, sim_timestep_ms, float_to_fixed, **kwargs):
    # Copy values and divide by timestep
    scaled_vals = deepcopy(values)
    scaled_vals /= sim_timestep_ms

    # Convert to fixed-point and return
    return float_to_fixed(scaled_vals)


def exp_decay(values, sim_timestep_ms, float_to_fixed, **kwargs):
    # Copy values and calculate exponential decay
    exp_decay_vals = deepcopy(values)
    exp_decay_vals = la.exp(-sim_timestep_ms / exp_decay_vals)

    # Convert to fixed-point and return
    return float_to_fixed(exp_decay_vals)


def exp_init(values, sim_timestep_ms, float_to_fixed, **kwargs):
    # Copy values and calculate exponential init
    exp_init_vals = deepcopy(values)
    exp_init_vals = 1.0 - la.exp(-sim_timestep_ms / exp_init_vals)
    exp_init_vals *= (values / sim_timestep_ms)

    # Convert to fixed-point and return
    return float_to_fixed(exp_init_vals)


def rate_isi(values, sim_timestep_ms, float_to_fixed, **kwargs):
    # Copy values and convert rates to isis
    isi_vals = deepcopy(values)
    isi_vals = 1000.0 / (isi_vals * sim_timestep_ms)

    # Convert to fixed-point and return
    return float_to_fixed(isi_vals)


def rate_exp_minus_lambda(values, sim_timestep_ms, float_to_fixed, **kwargs):
    # Copy values and convert to spikes per-tick
    lambda_vals = deepcopy(values)
    lambda_vals = (lambda_vals * sim_timestep_ms) / 1000.0

    # Calculate exponential
    lambda_vals = la.exp(-1.0 * lambda_vals)

    # Convert to fixed point and return
    return float_to_fixed(lambda_vals)

def exp_decay_lut(values, num_entries, time_shift, sim_timestep_ms,
                  float_to_fixed, **kwargs):
    # Determine the time step of the LUT in milliseconds
    timestep_ms = sim_timestep_ms * float(2 ** time_shift)

    # Build a lazy array of times to calculate decay values for
    time_ms = la.larray(
        np.arange(0.0, -timestep_ms * float(num_entries), -timestep_ms))

    # Calculate exponential decay
    values.shape = time_ms.shape
    decay_vals = la.exp(time_ms / values)

    # Check last entry is zero(ish)
    if decay_vals[-1] > (1.0 / float(1 << float_to_fixed.n_frac)):
        logger.warn("Exponential decay LUT too short - last entry:%f, "
                    "num_entries:%u, time shift:%u, time step:%fms and "
                    "tau:%fms", decay_vals[-1], num_entries, time_shift,
                    sim_timestep_ms, values[0])

    # Convert to fixed-point and return
    return float_to_fixed(decay_vals)

def random_seed(max_value, num_words, **kwargs):
    # Return random vector
    # **TODO** these should really be generated by a PyNN-specific RNG
    return la.larray(np.random.randint(max_value, size=num_words))

def its_lut(distribution, n_frac):
    # Calculate floating point range this represents
    q = np.arange(0.0, 1.0, 1.0 / float(1 << n_frac))

    # Return inverse CDF
    return la.larray(distribution(q))

# Various functions bound to standard fixed point types
s1615_time_multiply = partial(time_multiply, float_to_fixed=float_to_s1615_no_copy)
s1615_exp_decay = partial(exp_decay, float_to_fixed=float_to_s1615_no_copy)
u032_exp_decay = partial(exp_decay, float_to_fixed=float_to_u032_no_copy)
s1615_exp_init = partial(exp_init, float_to_fixed=float_to_s1615_no_copy)
s1615_rate_isi = partial(rate_isi, float_to_fixed=float_to_s1615_no_copy)
u032_rate_exp_minus_lambda = partial(rate_exp_minus_lambda, float_to_fixed=float_to_u032_no_copy)
s411_exp_decay_lut = partial(exp_decay_lut, float_to_fixed=float_to_s411_no_copy)
mars_kiss_64_random_seed = partial(random_seed, max_value=0x7FFFFFFF, num_words=4)
