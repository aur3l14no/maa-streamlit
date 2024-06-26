import pathlib

MAA_STREAMLIT_STATE_DIR = pathlib.Path(__file__).parent.parent / "data"
MAA_CORE_DIR = MAA_STREAMLIT_STATE_DIR / "maa-core"

LOGGER_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "{extra} - <level>{message}</level>"
)

CONCISE_LOGGER_FORMAT = (
    "<green>{time:ddd HH:mm:ss}</green> | "
    "<level>{level: <4}</level> | "
    "<level>{message}</level>"
)
