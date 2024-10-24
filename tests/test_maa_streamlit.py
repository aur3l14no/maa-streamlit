import datetime as dt

import maa_streamlit.schedule


def test_cron_delta():
    cron_delta = maa_streamlit.schedule.cron_delta
    assert cron_delta(dt.time(), dt.datetime(2000, 1, 1, 23, 59, 30)) == dt.timedelta(
        seconds=30
    )
    assert cron_delta(dt.time(), dt.datetime(2000, 1, 1, 0, 0, 30)) == dt.timedelta(
        seconds=30
    )
    assert cron_delta(dt.time(), dt.datetime(2000, 1, 1, 0, 1, 30)) == dt.timedelta(
        seconds=90
    )
