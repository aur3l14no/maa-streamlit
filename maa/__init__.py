import json
import multiprocessing as mp
import threading

import maa_streamlit


class MaaProxy:
    def __init__(self, device: maa_streamlit.data.Device):
        self.device = device
        ctx = mp.get_context("spawn")
        self.parent_conn, self.child_conn = ctx.Pipe()
        self.process = ctx.Process(
            target=MaaProxy.target, args=(device, self.child_conn), daemon=True
        )
        self.process.start()
        self.log_path = None
        self.lock = threading.Lock()

    @staticmethod
    def target(device: maa_streamlit.data.Device, child_conn: mp.Pipe):
        # logger
        from loguru import logger

        from .asst.asst import Asst
        from .asst.utils import InstanceOptionType, Message

        logger = logger.bind(device=device.name)
        logger.add(
            maa_streamlit.consts.MAA_STREAMLIT_STATE_DIR / f"{device.name}.log",
            level="INFO",
            rotation="00:00",
            retention=2,
            format=maa_streamlit.consts.CONCISE_LOGGER_FORMAT,
            enqueue=True,
        )
        logger.add(
            maa_streamlit.consts.MAA_STREAMLIT_STATE_DIR / f"{device.name}.debug.log",
            level="DEBUG",
            rotation="00:00",
            retention=2,
            format=maa_streamlit.consts.LOGGER_FORMAT,
            enqueue=True,
        )

        # callback
        def make_callback():
            # TODO improve callback
            # ref https://github.com/MaaAssistantArknights/maa-cli/blob/main/maa-cli/src/run/callback/mod.rs
            # ref https://github.com/MaaAssistantArknights/maa-cli/blob/main/maa-cli/src/run/callback/summary.rs
            def my_callback(msg, details, _):
                m = Message(msg)
                d = json.loads(details.decode("utf-8"))
                details = d.get("details")
                what = d.get("what")
                try:
                    match m:
                        case (
                            Message.TaskChainStart
                            | Message.TaskChainCompleted
                            | Message.TaskChainError
                            | Message.TaskChainExtraInfo
                            | Message.TaskChainStopped
                        ):
                            logger.info(f"{m} {d['taskchain']}")
                        case Message.SubTaskCompleted:
                            match details.get("task"):
                                # case "StartButton2":
                                #     logger.info("[作战] +1")
                                case "AbandonAction":
                                    logger.info("[作战] 代理失败")
                                case "StartExplore":
                                    logger.info("[肉鸽] +1")
                                case "OfflineConfirm":
                                    logger.info("[游戏] 掉线")
                                case "Reclamation2Begin":
                                    if details.get("exec_times") == 1:
                                        logger.info("[演算] +1")
                        case Message.ConnectionInfo:
                            match what:
                                case "Connected":
                                    logger.info("[ADB] 连接成功")
                                case "FastestWayToScreencap":
                                    logger.info(
                                        f"[ADB] 截图耗时 {d['details'].get('cost')} ({d['details'].get('method')})"
                                    )
                        case Message.SubTaskExtraInfo:
                            # 公开招募
                            match what:
                                case "RecruitResult":
                                    logger.info(
                                        f"[公招] 结果 {'★' * d['details'].get('level')} {d['details'].get('tags')}"
                                    )
                                case "RecruitTagsDetected":
                                    logger.info(
                                        f"[公招] 标签 {d['details'].get('tags')}"
                                    )
                                case "RecruitSpecialTag":
                                    logger.info(
                                        f"[公招] 特殊标签 {d['details'].get('tag')}"
                                    )
                                case "RecruitRobotTag":
                                    logger.info(
                                        f"[公招] 机械标签 {d['details'].get('tag')}"
                                    )
                                case "RecruitTagsRefreshed":
                                    logger.info("[公招] 刷新")
                                # 基建
                                case "CustomInfrastRoomOperators":
                                    logger.info(
                                        f"[基建] {d['details'].get('facility')}@{d['details'].get('index')}: "
                                        f"{d['details'].get('names')}"
                                    )
                                # 仓库扫描
                                case "DepotInfo":
                                    if details["done"]:
                                        logger.info(
                                            f"[仓库] arkplanner {d['details']['arkplanner']['data']}"
                                        )
                                        logger.info(
                                            f"[仓库] lolicon {d['details']['lolicon']['data']}"
                                        )
                                # 作战
                                case "StageDrops":
                                    drops_string = " ".join(
                                        [
                                            f"{drop['itemName']}*{drop['quantity']}"
                                            for drop in details["drops"]
                                        ]
                                    )
                                    if d["details"].get("stars") == 3:
                                        logger.info(
                                            f"[作战] {d['details']['stage']['stageCode']} {'★' * d['details']['stars']} {drops_string}"
                                        )
                                    else:
                                        logger.warning(
                                            f"[作战] {d['details']['stage']['stageCode']} {'★' * d['details']['stars']} {drops_string}"
                                        )
                                # 理智
                                case "SanityBeforeStage":
                                    logger.info(
                                        f"[理智] {details.get('current_sanity')} / {details.get('max_sanity')}"
                                    )
                                case "UseMedicine":
                                    count = details.get("count")
                                    if details.get("is_expiring"):
                                        logger.info(
                                            f"[理智] 使用 {count} 药水 (即将过期)"
                                        )
                                    else:
                                        logger.info(f"[理智] 使用 {count} 药水")

                    logger.debug(json.dumps({"msg": str(m), "details": d}))
                except Exception as e:
                    logger.error(e)
                    logger.error(json.dumps({"msg": str(m), "details": d}))

            return Asst.CallBackType(my_callback)

        asst_callback = make_callback()

        # core
        Asst.load(
            path=maa_streamlit.consts.MAA_CORE_DIR,
            incremental_path=maa_streamlit.consts.MAA_CORE_DIR / "cache",
        )
        asst = Asst(callback=asst_callback)
        # TODO make it configurable
        asst.set_instance_option(InstanceOptionType.touch_type, "maatouch")
        if not asst.connect("adb", device.address, device.config):
            logger.error(f"Failed to connect {json.dumps(device)}")
            raise Exception(f"Failed to connect {json.dumps(device)}")

        # work loop
        try:
            while True:
                func, args = child_conn.recv()
                result = None
                if func is None:
                    logger.error("Received None as func")
                    break
                elif func == "shutdown":
                    logger.info(f"Maa worker loop for {device} is shutting down.")
                    child_conn.send(True)
                    break
                elif func == "append_task":
                    result = asst.append_task(*args)
                elif func == "start":
                    result = asst.start()
                elif func == "stop":
                    result = asst.stop()
                elif func == "running":
                    result = asst.running()
                child_conn.send(result)
        except KeyboardInterrupt:
            logger.warning("Ctrl-C, Goodbye~")
            pass
        except Exception as e:
            logger.error(f"Uncaught error {e}")

    def append_task(self, task, params) -> int:
        with self.lock:
            self.parent_conn.send(
                (
                    "append_task",
                    (task, params),
                )
            )
            return self.parent_conn.recv()

    def start(self) -> bool:
        with self.lock:
            self.parent_conn.send(("start", ()))
            return self.parent_conn.recv()

    def stop(self) -> bool:
        with self.lock:
            self.parent_conn.send(("stop", ()))
            return self.parent_conn.recv()

    def running(self) -> bool:
        with self.lock:
            self.parent_conn.send(("running", ()))
            return self.parent_conn.recv()

    def shutdown(self) -> bool:
        with self.lock:
            if not self.stop():
                return False
            self.parent_conn.send(("shutdown", ()))
            if not self.parent_conn.recv():
                return False
            self.process.join(5)
            return self.process.exitcode == 0


class MaaUpdater:
    def __init__(self) -> None:
        self.lock = threading.Lock()

    def update_core(self):
        from .asst.updater import Updater
        from .asst.utils import Version

        with self.lock:
            Updater(maa_streamlit.consts.MAA_CORE_DIR, Version.Beta).update()

    def update_ota(self):
        import urllib

        with self.lock:
            ota_tasks_url = (
                "https://ota.maa.plus/MaaAssistantArknights/api/resource/tasks.json"
            )
            ota_tasks_path = (
                maa_streamlit.consts.MAA_CORE_DIR / "cache" / "resource" / "tasks.json"
            )
            ota_tasks_path.parent.mkdir(parents=True, exist_ok=True)
            with open(ota_tasks_path, "w", encoding="utf-8") as f:
                with urllib.request.urlopen(ota_tasks_url) as u:
                    f.write(u.read().decode("utf-8"))
