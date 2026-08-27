import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv("config_admins.env", override=True)

ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]


def reload_admin_ids():
    global ADMIN_IDS
    ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

TOKEN = "8960816480:AAFU2SzZYCCGMX2BnPw320atkXQfo8xljtE"
INFO_ID = -1004352329885
NEWS_ID = -1003942425064
REPS_ID = -1004262560990
ADMIN_ID = [8760110337, 7566692727, 8405558443,5025230115]