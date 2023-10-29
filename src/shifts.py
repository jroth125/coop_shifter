import requests
import datetime
import time
import logging
import os
import dateparser
import dotenv
from typing import List, NamedTuple
from bs4 import Tag
from coop_session import CoopSession
from url_constants import TEXTBELT_URL

logger: logging.Logger = logging.getLogger(__name__)
dotenv.load_dotenv()

SHIFT_TIME_HRS: float = 2.75


class CoopShift(NamedTuple):
    shift_name: str
    shift_time: str


class ShiftNotifier:
    PAGES: int = 6
    MAX_SHIFT_MSG_LENGTH = 95
    RETEXT_EVERY_SECS: int = 60 * 60  # 1 hour

    def __init__(self, timeout_secs: int, phone_num: int) -> None:
        self.last_texted_time: float = 0.0
        self.timeout_secs: int = timeout_secs
        self.start_time = time.time()
        self.phone_num: int = phone_num

    def fetch_eligible_shifts(
        self,
        shift_date: datetime.date,
        start_hour: int,
        end_hour: int,
        shift_name: str,
        keep_session_alive: bool,
        sleep_time_secs: int,
    ) -> List[str]:
        while self._is_not_timed_out():
            with CoopSession(
                keep_session_alive=keep_session_alive,
                username=os.getenv("COOP_USERNAME"),
                password=os.getenv("COOP_PASSWORD"),
            ) as coop_sesh:
                shifts: List[CoopShift] = self._get_available_shifts(
                    coop_sesh=coop_sesh,
                    shift_date=shift_date,
                    start_hour=start_hour,
                    end_hour=end_hour,
                    shift_name=shift_name,
                )
                if not shifts:
                    logger.info(f"No shifts found - will retry in {sleep_time_secs}")
                    time.sleep(sleep_time_secs)
                    continue

                human_readable_shifts = "\n".join(
                    [f"{shift.shift_time}: {shift.shift_name}" for shift in shifts]
                )
                print(f"====== PRINTING SHIFT TIMES ====== \n{human_readable_shifts}")
                self.maybe_send_text(human_readable_shifts)

        logger.info("Timed out! Ending... ")

    def _is_not_timed_out(self):
        return time.time() - self.start_time <= self.timeout_secs

    def _get_available_shifts(
        self,
        coop_sesh: CoopSession,
        shift_date: datetime.date,
        start_hour,
        end_hour,
        shift_name,
    ) -> List[CoopShift]:
        s: requests.Session = coop_sesh.session

        shift_doms = [
            coop_sesh.get_shifts_page_dom(s, page) for page in range(self.PAGES)
        ]
        for shift_dom in shift_doms:
            shifts_grid = shift_dom.find("div", {"class": "grid-container"})
            try:
                shifts = next(
                    col.find_all("a", {"class": "shift"})
                    for col in shifts_grid.find_all(
                        "div", {"class": "col"}, recursive=False
                    )
                    if self._get_date_from_col(col) == shift_date
                )
                logger.info(
                    "Found shifts page for chosen date. Now searching for matching shifts"
                )
                return self._get_matching_shifts(
                    all_shifts=shifts,
                    shift_name=shift_name,
                    start_hour=start_hour,
                    end_hour=end_hour,
                )

            except StopIteration:
                continue

        raise AssertionError("No date on coop site matched the given one!")

    def maybe_send_text(self, human_readable_shifts: str):
        time_now = time.time()

        first_time_texting: bool = not self.last_texted_time
        have_already_texted: bool = (
            time_now - self.last_texted_time >= self.RETEXT_EVERY_SECS
        )
        if first_time_texting or have_already_texted:
            logger.info("Sending text message to coop member!")
            shift_msg = (
                f"{human_readable_shifts}"
                if len(human_readable_shifts) <= self.MAX_SHIFT_MSG_LENGTH
                else f"(too many shifts for text)"
            )
            full_msg = (
                f"Coop shifts available! \n{shift_msg}\n\n"
                + "Check now: https://members.foodcoop.com/services/shifts"
            )
            res = requests.post(
                TEXTBELT_URL,
                {
                    "phone": str(self.phone_num),
                    "message": full_msg,
                    "key": os.getenv("SMS_API_KEY"),
                },
            )
            logger.debug("SMS response: ", res.json())
            self.last_texted_time = time_now
            logger.info(f"Response: {res}")
        else:
            logger.info("Not sending text")

    def _get_matching_shifts(
        self, all_shifts: List[str], shift_name: str, start_hour: int, end_hour: int
    ) -> List[str]:
        eligible_shifts: List[CoopShift] = []
        for shift in all_shifts:
            time_raw = shift.find("b", recursive=False).string
            parsed_shift_time = dateparser.parse(time_raw)

            valid_shift_starttime: bool = parsed_shift_time.hour >= start_hour
            valid_shift_endtime: bool = (
                end_hour >= parsed_shift_time.hour + SHIFT_TIME_HRS
            )
            # shifts with "my_shift" class are ones you have already signed up for
            not_signed_up_for_yet: bool = "my_shift" not in shift.attrs["class"]

            if valid_shift_starttime and valid_shift_endtime and not_signed_up_for_yet:
                cur_shift_name = str(shift.contents[2]).splitlines()[2].strip()[:-2]
                if (shift_name == "all") or (
                    cur_shift_name.lower() == shift_name.lower()
                ):
                    eligible_shifts.append(
                        CoopShift(
                            shift_name=cur_shift_name,
                            shift_time=parsed_shift_time.strftime("%H:%M"),
                        )
                    )
        return eligible_shifts

    @staticmethod
    def _get_date_from_col(col: Tag) -> datetime.date:
        raw_date = col.find("p").find("b").string
        date = dateparser.parse(raw_date)
        logger.debug(f"Date for current column is {date}")
        return date
