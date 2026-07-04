import os
import re
from datetime import datetime
import pandas as pd

CSV_COLUMN_NAMES = ["Date", "Time", "Price", "Volume", "Open Interest"]
# only the date, time and price are referred to
UNDERLIERS = ["NIFTY", "BANKNIFTY"]

FUTURES_FILE_SUFFIX = "-I.csv"

def load_csv(filepath):
    """
    This function reads the csv file which is raw and returna a dataframe with the necessary
    column names
    """
    data = pd.read_csv(filepath, header=None, names=CSV_COLUMN_NAMES)

    data["timestamp"] = pd.to_datetime(
        data["Date"].astype(str) + " " + data["Time"],
        format="%Y%m%d %H:%M:%S"
    )

    data = data.drop_duplicates(subset="timestamp", keep="last")

    data = data.set_index("timestamp")

    data = data.drop(columns=["Date", "Time"])

    return data

def parse_instrument_filename(filename):
    """
    Takes the file name NIFTY22110314550PE and splits as follows:
    underlier: NIFTY, expiry: 221103, strike: 14550, option_type: PE
    """
    name_without_extension = filename.replace(".csv", "")

    pattern = r"^([A-Z]+)(\d{6})(\d+)(CE|PE)$"
    match = re.match(pattern, name_without_extension)

    if match is None:
        return None

    underlier = match.group(1)
    expiry = match.group(2)
    strike = int(match.group(3))
    option_type = match.group(4)

    return {
        "underlier": underlier,
        "expiry": expiry,
        "strike": strike,
        "option_type": option_type,
        "full_name": name_without_extension,
    }

def load_futures_for_date(date_folder, underlier):
    """
    Constructs the necessary file we want like NIFTY-1 in Futures folder of
    NSE_20221101 and uses load_csv function to return the price series dataframe.
    """
    filename = underlier + FUTURES_FILE_SUFFIX
    filepath = os.path.join(date_folder, "Futures (Continuous)", filename)

    if not os.path.exists(filepath):
        print(f"  [WARNING] Futures file not found: {filepath}")
        return pd.DataFrame()

    return load_csv(filepath)


def build_options_index_for_date(date_folder):
    """
    Instead of loading all the thousands of file in each option folder every second, 
    a lookup dictionary is created so we can access the file using its filename in O(1) time.
    """
    options_folder = os.path.join(date_folder, "Options")

    if not os.path.exists(options_folder):
        print(f"  [WARNING] Options folder not found: {options_folder}")
        return {}

    instrument_index = {}

    for filename in os.listdir(options_folder):
        if not filename.endswith(".csv"):
            continue

        instrument_info = parse_instrument_filename(filename)
        if instrument_info is None:
            continue

        instrument_info["filepath"] = os.path.join(options_folder, filename)
        instrument_index[instrument_info["full_name"]] = instrument_info

    return instrument_index

def get_nearest_expiry(options_index, underlier, trade_date):
    """
   For a given underlier on a particular day, we find all the valid expiry
   days first, then the closest expiry date is found.
    """

    all_expiries = set()
    for info in options_index.values():
        if info["underlier"] == underlier:
            all_expiries.add(info["expiry"])

    if not all_expiries:
        return None

    trade_date_obj = datetime.strptime(trade_date, "%Y%m%d").date()

    upcoming_expiries = []
    for expiry_str in all_expiries:
        expiry_date_obj = datetime.strptime("20" + expiry_str, "%Y%m%d").date()
        if expiry_date_obj >= trade_date_obj:
            upcoming_expiries.append((expiry_date_obj, expiry_str))

    if not upcoming_expiries:
        return None

    upcoming_expiries.sort(key=lambda pair: pair[0])
    nearest_expiry_str = upcoming_expiries[0][1]

    return nearest_expiry_str

def get_atm_strike_instrument(options_index, underlier, expiry, futures_price, option_type):
    """
    This function finds the instrument which has the underlier we want, the closest expiry
    date and either CE or PE as per want we require.
    """
    matching_instruments = [
        info for info in options_index.values()
        if info["underlier"] == underlier
        and info["expiry"] == expiry
        and info["option_type"] == option_type
    ]

    if not matching_instruments:
        return None

    closest_instrument = min(
        matching_instruments,
        key=lambda info: abs(info["strike"] - futures_price)
    )

    return closest_instrument["full_name"]

def get_trading_dates(data_root):
    """
    Return all the dates available in the month , eg like NSE_20221101, etc
    """
    trading_dates = []

    for folder_name in os.listdir(data_root):
        if folder_name.startswith("NSE_") and len(folder_name) == 12:
            date_str = folder_name[len("NSE_"):]
            trading_dates.append(date_str)

    return sorted(trading_dates)
