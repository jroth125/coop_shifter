# coop_shifter

`coop_shifter` is a a Python CLI for Park Slope Food Coop members to notify them when the shift they want opens up.

## Setup
Save the number you will get texts from: 1-903-321-4254

Ensure you have Make and Python3.11 installed on your device. Then, install the dependencies you need:

```
make install
```

Make sure you have an API key from textbelt. You can get one [here](https://textbelt.com/purchase/?generateKey=1):

After cloning the `coop_shifter` repo, ensure you have a `.env`` file in the root of the repo's directory. It should look like this:

```
SMS_API_KEY="<api key from textbelt>"
COOP_USERNAME="<your coop username>"
COOP_PASSWORD="<your coop password>"
```

Now you should be all set

## How to use

See all the arguments you can use by running 

```
$ src/main.py --help
```

```
options:
  -h, --help            show this help message and exit
  -d DATE, --date DATE  Date in mm-dd-yyyy format you want your shift to be. E.g. 04-13-2022
  -s START_HOUR, --start-hour START_HOUR
                        Earliest time (1-24) shift could start (inclusive)
  -e END_HOUR, --end-hour END_HOUR
                        Latest time (1-24) shift the shift could end (inclusive).
  --shift SHIFT         The name of the shift you want, e.g. 'checkout'
  --keep-session-alive  Mainly for testing purposes. Persists request session to disk sowe don't create too many of them
  --sleep-time-secs SLEEP_TIME_SECS
                        How many seconds the program should sleep before checking latest shifts
  --timeout-mins TIMEOUT_MINS
                        When you want this script to stop
  --phone-num PHONE_NUM
                        Your phone number
  --log-level {DEBUG,INFO,WARNING,ERROR}
                        Override log level to change verbosity of logs.
```

Let's say you want to get a checkout coop shift that starts at or after 11am and ends at or after 3pm on October 2, 2023. You would run this as follows. Before running, here are a couple notes to keep in mind:
- the hours are in military time (right now, we only support whole integers here, so something like `-s 11:30` wouldn't work)
- the shift name must be exactly how it's listed on the coop website without the little emojis (common ones are `checkout`, `stocking`, `lifting`, `producer`, `cleaning`, `bulk`)
- the `--phone-num` arg must have no dashes. This is the number that will get texted when we find a shift!


```
$ python3 main.py -d 10-02-2023 -s 11 -e 15 --shift checkout --phone-num 1234567789
```


If you want *any* shift and don't care which one it is, you can just leave out the `--shift` arg:

```
$ python3 main.py -d 10-02-2023 -s 11 -e 15 
```

## How it works

Once run, the script scrapes the Coop's shift calendar every 20 seconds. If it finds a shift, you should get a text alerting you to this. 

Some things to keep in mind:
- If the script finds a shift, it will text you once and not text you again for another 1 hour (this is to prevent overloading your phone with spammy texts). This isn't configurable right now, but it's something I'll work on soon
- If you run this on your computer (e.g. a macbook) and it enters the lockscreen, it will stop checking the Coop website. It's best to run this on a computer that never falls asleep, like an AWS EC2 instance
- The script will die after its timeout of a few hours
