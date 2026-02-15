"""Configuration values for per-line fairness checks."""

DEFAULT_MEDIAN_DELTA = {"DF": 0.20, "MF": 0.20, "ST": 0.65}
DEFAULT_IQR_DELTA = {"DF": 0.80, "MF": 0.40, "ST": 1.30}
MAX_RETRIES = 3
