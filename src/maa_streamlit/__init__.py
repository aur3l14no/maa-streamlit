from loguru import logger

from . import consts

logger = logger.bind(module="maa_streamlit")
logger.add(
    consts.MAA_STREAMLIT_STATE_DIR / "maa_streamlit.log",
    level="INFO",
    format=consts.LOGGER_FORMAT,
    filter=lambda record: record["extra"].get("module") == "maa_streamlit",
    enqueue=True,
)
