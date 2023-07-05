import os
from sys import warnoptions

if not warnoptions: # if user hasn't passed explicit warning settings
    import warnings
    from typing import Literal
    WARN_LEVEL: Literal['default', 'error', 'ignore', 'always', 'module', 'once']
    if ENVIRONMENT_TYPE == "development":
        WARN_LEVEL = 'error'
    elif ENVIRONMENT_TYPE == "production":
        WARN_LEVEL = 'always'
    else:
        raise Exception(f"Unknown environment type {ENVIRONMENT_TYPE}")

    warnings.simplefilter(WARN_LEVEL) # Change the filter in this process
    os.environ["PYTHONWARNINGS"] = WARN_LEVEL # Also affect subprocesses
