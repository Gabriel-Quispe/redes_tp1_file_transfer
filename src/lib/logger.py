import logging

def configure_logger(verbose=False, quiet=True):
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    logging.basicConfig(
        level=level,
        format='[%(levelname)s] %(message)s'
    )
logger = logging.getLogger("RDT")