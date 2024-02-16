import json
import urllib.request

from loguru import logger

import maa_streamlit
import maa_streamlit.adb
import maa_streamlit.consts as consts

from .asst.asst import Asst
from .asst.updater import Updater
from .asst.utils import InstanceOptionType, Message, Version

# keep loggers from gc
callback_dict = {}


def make_callback(logger):
    # TODO improve callback
    # ref https://github.com/MaaAssistantArknights/maa-cli/blob/main/maa-cli/src/run/callback/mod.rs
    # ref https://github.com/MaaAssistantArknights/maa-cli/blob/main/maa-cli/src/run/callback/summary.rs
    def my_callback(msg, details, _):
        m = Message(msg)
        d = json.loads(details.decode("utf-8"))

        try:
            if m == Message.TaskChainStart:
                pass
            elif m == Message.SubTaskCompleted:
                task = d["details"].get("task")
                if task == "StartButton2":
                    logger.info("[作战] +1")
                elif task == "AbandonAction":
                    logger.info("[作战] 代理失败")
                elif task == "StartExplore":
                    logger.info("[肉鸽] +1")
                elif task == "MissionFailedFlag":
                    logger.info("[肉鸽] 失败")
                elif task == "MissionCompletedFlag":
                    logger.info("[肉鸽] 成功")
                elif task == "OfflineConfirm":
                    logger.info("[游戏] 掉线")
            elif m == Message.ConnectionInfo:
                if d["what"] == "Connected":
                    logger.info("[ADB] 连接成功")
                if d["what"] == "FastestWayToScreencap":
                    logger.info(
                        f"[ADB] 截图耗时 {d['details'].get('cost')} ({d['details'].get('method')})"
                    )
            elif m == Message.SubTaskExtraInfo:
                # 公开招募
                what = d["what"]
                if what == "RecruitResult":
                    logger.info(
                        f"[公招] 结果 {'★' * d['details'].get('level')} {d['details'].get('tags')}"
                    )
                elif what == "RecruitTagsDetected":
                    logger.info(f"[公招] 检测到标签 {d['details'].get('tags')}")
                elif what == "RecruitSpecialTag":
                    logger.info(f"[公招] 检测到标签 {'★' * d['details'].get('tag')}")
                elif what == "RecruitRobotTag":
                    logger.info(f"[公招] 检测到标签 {'★' * d['details'].get('tag')}")
                elif what == "RecruitTagsRefreshed":
                    logger.info("[公招] 刷新")
                # 基建
                elif what == "CustomInfrastRoomOperators":
                    logger.info(
                        f"[基建] {d['details'].get('facility')}@{d['details'].get('index')}: "
                        f"{d['details'].get('names')}"
                    )

            logger.debug(json.dumps({"msg": str(m), "details": d}))
        except Exception:
            logger.error(json.dumps({"msg": str(m), "details": d}))

    return Asst.CallBackType(my_callback)


def update_core():
    Updater(consts.MAA_CORE_DIR, Version.Beta).update()


def update_ota():
    ota_tasks_url = "https://ota.maa.plus/MaaAssistantArknights/api/resource/tasks.json"
    ota_tasks_path = consts.MAA_CORE_DIR / "cache" / "resource" / "tasks.json"
    ota_tasks_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ota_tasks_path, "w", encoding="utf-8") as f:
        with urllib.request.urlopen(ota_tasks_url) as u:
            f.write(u.read().decode("utf-8"))


def init_core():
    Asst.load(path=consts.MAA_CORE_DIR, incremental_path=consts.MAA_CORE_DIR / "cache")


def new_asst(device) -> Asst:
    # create logger
    device_logger = logger.bind(device=device)
    device_logger.add(
        maa_streamlit.consts.MAA_STREAMLIT_STATE_DIR / f"{device}.log",
        level="INFO",
        rotation="1 day",
        retention=2,
        format=consts.CONCISE_LOGGER_FORMAT,
        diagnose=False,
        filter=lambda record, device=device: record["extra"].get("device") == device,
    )
    device_logger.add(
        maa_streamlit.consts.MAA_STREAMLIT_STATE_DIR / f"{device}.debug.log",
        level="DEBUG",
        rotation="1 day",
        retention=2,
        format=consts.LOGGER_FORMAT,
        diagnose=True,
        filter=lambda record, device=device: record["extra"].get("device") == device,
    )

    callback_dict[device] = make_callback(device_logger)
    asst = Asst(callback=callback_dict[device])
    asst.set_instance_option(InstanceOptionType.touch_type, "maatouch")
    if asst.connect("adb", device, "GeneralWithoutScreencapErr"):
        return asst
    else:
        raise Exception(f"Failed to connect {device}")
