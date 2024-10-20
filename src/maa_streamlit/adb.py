import subprocess as sp
import time
from io import BytesIO
from typing import Optional

import streamlit as st
from loguru import logger
from PIL import Image

from . import data


class AdbProxy:
    ARKNIGHTS_BUNDLE_NAME = "com.hypergryph.arknights"
    TTL = "5s"

    def __init__(self, profile: data.Profile) -> None:
        self.profile = profile

    def _st_hash(self):
        return self.profile.name

    @st.cache_data(ttl=TTL, hash_funcs={"maa_streamlit.adb.AdbProxy": _st_hash})
    def screenshot(self) -> bytes:
        # can it be faster? we only need a
        time_start = time.time()
        img_bytes = sp.check_output(
            [
                self.profile.connection.adb_path,
                "-s",
                self.profile.connection.device,
                "exec-out",
                "screencap -p 2>/dev/null",
            ]
        )
        img = Image.open(BytesIO(img_bytes))
        img_thumbnail = img.resize((768, 432))
        logger.trace(
            f"Screenshot of '{self.profile.name}' took {time.time() - time_start}"
        )
        return img_thumbnail

    def force_close(self) -> None:
        sp.run(
            [
                self.profile.connection.adb_path,
                "-s",
                self.profile.connection.device,
                "shell",
                f"am force-stop {self.ARKNIGHTS_BUNDLE_NAME} && sleep 1",
            ]
        )

    def pid(self) -> Optional[int]:
        try:
            pid_s = sp.check_output(
                [
                    self.profile.connection.adb_path,
                    "-s",
                    self.profile.connection.device,
                    "shell",
                    f"pidof {self.ARKNIGHTS_BUNDLE_NAME}",
                ],
                encoding="utf8",
            )
            return int(pid_s.strip())
        except sp.CalledProcessError:
            return None
        except ValueError:
            logger.error(f"[ADB] Cannot parse {pid_s}")
            return None

    def app_running(self) -> bool:
        return self.pid() is not None
