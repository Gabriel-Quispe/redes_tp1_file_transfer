import logging
def show_stats(final_time, size):    
    throughput=0
    if final_time>0:
        throughput=(size)/final_time
    logger.info("Transmisión finalizada con exito.")
    logger.info(f"Estadísticas")
    logger.info(f"Tiempo: {final_time:.2f} segundos")
    logger.info(f"Tamaño: {size / 1024:.2f} KB")
    logger.info(f"Throughput promedio: {throughput:.2f} Bps")
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