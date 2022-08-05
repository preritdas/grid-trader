"""
Reads keys.ini and parses values into their appropriate types,
to be referneced by other modules.
"""
import configparser
import os  # ensure file exists


# Ensure keys.ini file has been created
if not os.path.exists(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys.ini')
):
    raise Exception(
        "You must create a keys.ini, in the format of keys (sample).ini, "
        "containing your API keys and contact information. "
        "See the GitHub repository to understand the behavior of each attribute."
    )


# Read keys.ini file
keys = configparser.ConfigParser()
keys.read('keys.ini')


class Alpaca:
    """
    Trading API.
    """
    api_key = keys['Alpaca']['api_key']
    api_secret = keys['Alpaca']['api_secret']
    base_url = keys['Alpaca']['base_url']
