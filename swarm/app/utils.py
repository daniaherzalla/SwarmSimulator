"""Utility functions and classes."""

import numpy as np
import math
from . import params


def randrange(a, b):
    """Random number between a and b."""
    return a + np.random.random() * (b - a)


def px_to_grid(px_pos):
    """Convert pixel position to grid position."""
    return px_pos[0] / params.COL, px_pos[1] / params.ROW


def grid_to_px(grid_pos):
    """Convert grid position to pixel position."""
    if len(grid_pos) > 2:
        return grid_pos[0] * params.COL, grid_pos[1] * params.ROW, grid_pos[2]
    else:
        return grid_pos[0] * params.COL, grid_pos[1] * params.ROW


def norm(vector):
    """Compute the norm of a vector."""
    return math.sqrt(vector[0]**2 + vector[1]**2)


def norm2(vector):
    """Compute the square norm of a vector."""
    return vector[0] * vector[0] + vector[1] * vector[1]


def dist2(a, b):
    """Return the square distance between two vectors.

    Parameters
    ----------
    a : np.array
    b : np.array
    """
    # print("a: ", a)
    # print("b: ", b)
    return norm2(a - b)


def dist(a, b):
    """Return the Euclidean distance between two vectors.

    Parameters
    ----------
    a : np.array: A 2D or 3D position vector.
    b : np.array: A 2D or 3D position vector.
    """
    return norm(a - b)


def normalize(vector, pre_computed=None):
    """Return the normalized version of a vector.

    Parameters
    ----------
    vector : np.array
    pre_computed : float, optional
        The pre-computed norm for optimization. If not given, the norm
        will be computed.
    """
    n = pre_computed if pre_computed is not None else norm(vector)
    if n < 1e-13:
        return np.zeros(2)
    else:
        return np.array(vector) / n


# def truncate(vector, max_length):
#     """Truncate the length of a vector to a maximum value."""
#     n = norm(vector)
#     if n > max_length:
#         return normalize(vector, pre_computed=n) * max_length
#     else:
#         return vector

def truncate(vector, max_length):
    """Truncate the length of a vector to a maximum value."""
    length = np.linalg.norm(vector)
    if length > max_length:
        return (vector / length) * max_length
    return vector


