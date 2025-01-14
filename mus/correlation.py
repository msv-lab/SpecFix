import numpy as np


def point_biserial_correlation(x, y):
    # Convert inputs to NumPy arrays
    x = np.asarray(x, dtype=float)

    y = [int(label) for label in y]
    y = np.asarray(y, dtype=float)

    # Basic checks
    if x.shape[0] != y.shape[0]:
        raise ValueError("x and y must have the same length.")
    if not np.isin(y, [0, 1]).all():
        raise ValueError("y must contain only 0 or 1 values.")

    # Proportion of 1-labels
    p = np.mean(y)
    if p == 0.0 or p == 1.0:
        raise ValueError("y contains only one type of label (all 0s or all 1s). "
                         "Point-biserial correlation is undefined.")
    q = 1.0 - p

    # Mean of X for the two groups
    x1_mean = np.mean(x[y == 1])
    x0_mean = np.mean(x[y == 0])

    # Standard deviation of the entire array X
    s = np.std(x, ddof=1)  # ddof=1 for sample standard deviation

    # Point-biserial correlation
    r_pb = ((x1_mean - x0_mean) / s) * np.sqrt(p * q)
    return r_pb
