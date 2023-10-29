import requests
import shelve
import logging
import datetime

from bs4 import BeautifulSoup
from typing import List, Optional, Type
from types import TracebackType

from url_constants import BASE_URL, LOGIN_URL, CSRF_KEY, SHIFTS_URL, EXTRA_DATA_URL


logger: logging.Logger = logging.getLogger(__name__)


class CoopSession:
    SESSION_KEY: str = "shifter_session"
    DB_PATH: str = "/tmp/shifter_session_db"
    TEXT_EVERY_SECS: int = 60 * 60  # 1 hour

    def __init__(self, keep_session_alive: bool, username: str, password: str) -> None:
        self.keep_session_alive: bool = keep_session_alive
        self.text_sent_timestamp: int = 0
        self.username: str = username
        self.password: str = password

    def __enter__(self) -> None:
        with shelve.open(self.DB_PATH) as db:
            if self.SESSION_KEY not in db:
                logger.info("Creating new session")
                self.session = requests.Session()
                self._login()
            else:
                session = db[self.SESSION_KEY]
                logger.info("Grabbed session from local DB")
                if not self._does_session_still_work(session):
                    logger.info("Session from DB does not work. Creating new one")
                    self.session = requests.Session()
                    self._login()
                else:
                    self.session = session
                    logger.info("Session from DB still works")

        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        with shelve.open(self.DB_PATH) as db:
            if not self.keep_session_alive:
                if self.SESSION_KEY in db:
                    del db[self.SESSION_KEY]
                self.session.close()
            else:
                db[self.SESSION_KEY] = self.session

    def _login(self) -> None:
        site = self.session.get(f"{BASE_URL}{LOGIN_URL}")
        bs_content = BeautifulSoup(site.content, "html.parser")
        token = bs_content.find("input", {"name": CSRF_KEY})["value"]
        login_data = {
            "username": self.username,
            "password": self.password,
            "csrfmiddlewaretoken": token,
            "Submit": "Log In",
            "next": "",
        }
        self.session.headers.update(
            {
                "Referer": "https://members.foodcoop.com/services/login/",
                "Content-Type": "application/x-www-form-urlencoded",
                "Connection": "keep-alive",
            }
        )
        login_resp = self.session.post(f"{BASE_URL}{LOGIN_URL}", login_data)
        logger.info(f"Login status code response was: {login_resp.status_code}")

    @classmethod
    def get_shifts_page_dom(cls, s: requests.Session, page: int) -> BeautifulSoup:
        today_date = datetime.date.today().strftime("%Y-%m-%d")
        shifts_page = s.get(
            f"{BASE_URL}{SHIFTS_URL}/{page}/{EXTRA_DATA_URL}{today_date}"
        )
        return BeautifulSoup(shifts_page.content, "html.parser")

    @classmethod
    def _does_session_still_work(cls, s: requests.Session) -> bool:
        shifts_dom = cls.get_shifts_page_dom(s, 0)
        shift_text = shifts_dom.find(text="Shift Calendar")
        return bool(shift_text)
