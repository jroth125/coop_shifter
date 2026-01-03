import argparse
import datetime
import logging
import shifts
import dateparser


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument(
        "-d",
        "--date",
        type=str,
        required=True,
        help="Date in mm-dd-yyyy format you want your shift to be. E.g. 04-13-2022",
    )
    parser.add_argument(
        "-s",
        "--start-hour",
        type=int,
        required=True,
        help="Earliest time (1-24) shift could start (inclusive)",
    )
    parser.add_argument(
        "-e",
        "--end-hour",
        type=int,
        required=True,
        help="Latest time (1-24) shift the shift could end (inclusive).",
    )
    parser.add_argument(
        "--shift",
        type=str,
        default="all",
        help="The name of the shift you want, e.g. 'checkout'",
    )
    parser.add_argument(
        "--keep-session-alive",
        default=False,
        action="store_true",
        help=(
            "Mainly for testing purposes. Persists request session to disk so"
            "we don't create too many of them"
        ),
    )
    parser.add_argument(
        "--sleep-time-secs",
        default=20,
        type=int,
        help="How many seconds the program should sleep before checking latest shifts",
    )
    parser.add_argument(
        "--timeout-mins",
        default=60 * 5,  # 5 hours
        type=int,
        help="When you want this script to stop",
    )
    parser.add_argument(
        "--phone-num",
        required=True,
        type=int,
        help="Your phone number",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override log level to change verbosity of logs.",
    )
    return parser.parse_args()


def _set_logger(args: argparse.Namespace) -> logging.Logger:
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s")
    logger: logging.Logger = logging.getLogger()
    logger.setLevel(args.log_level)
    return logger


def _get_shift_date(args: argparse.Namespace, logger: logging.Logger) -> datetime.date:
    shift_date = dateparser.parse(
        args.date, settings={"DATE_ORDER": "MDY", "DEFAULT_LANGUAGES": ["en"]} # pyright: ignore[reportArgumentType]
    )
    assert shift_date is not None, (
        f"Date given of {args.date} couldn't be parsed! "
        "Was your date in MM-DD-YYYY format? E.g. 04-13-1994"
    )
    logger.info(f"Shift date set to {shift_date}")
    return shift_date


def main() -> None:
    args: argparse.Namespace = parse_args()
    logger = _set_logger(args)
    shift_date = _get_shift_date(args, logger)
    shift_start: int = args.start_hour
    shift_end: int = args.end_hour
    assert (
        shift_start + shifts.SHIFT_TIME_HRS <= shift_end
    ), "Shifts are 2:45 hrs long, but your start and end times allowed for less than that!"
    shift_notifier = shifts.ShiftNotifier(args.timeout_mins * 60, args.phone_num)
    shift_notifier.fetch_eligible_shifts(
        shift_date,
        args.start_hour,
        args.end_hour,
        args.shift.lower(),
        args.keep_session_alive,
        args.sleep_time_secs,
    )


if __name__ == "__main__":
    main()
