"""
Store Stax Access Key and Secret in Versent Innovation Account as Ssm Parameters
"""
import logging
import argparse
from os import environ

from utils import put_parameter

logging.getLogger().setLevel(environ.get("LOGLEVEL", logging.INFO))


# Populate environment variables STAX_ACCESS_KEY and STAX_ACCESS_KEY_SECRET with the credentials
# obtained from the Stax console (https://support.stax.io/hc/en-us/articles/4447111085583-Create-an-API-Token)

def populate_stax_secrets(stax_access_key, stax_access_key_secret):
    """Store Stax secrets in Ssm.
    """
    stax_parameters = {
        "/orchestrator/stax/access/key": {
            "description": "Stax Orchestrator Api Key",
            "value": stax_access_key
        },
        "/orchestrator/stax/access/key/secret": {
            "description": "Stax Orchestrator Api Key Secret",
            "value": stax_access_key_secret
        }
    }

    for k,v in stax_parameters.items():
        put_parameter(k, v["value"], description=v["description"], secure_string=True)

    logging.info("Successfully populated stax secrets!")

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="populate-stax-secrets",
        description="Populate stax secrets required by the Stax Orchestrator to interact with Stax Api." +
                    "See https://support.stax.io/hc/en-us/articles/4447111085583-Create-an-API-Token.",
    )

    parser.add_argument("--stax_access_key", help="Stax Access key")
    parser.add_argument("--stax_access_key_secret", help="Stax Access key")

    args = parser.parse_args()

    try:
        populate_stax_secrets(args.stax_access_key, args.stax_access_key_secret)
    except AttributeError:
        logging.error("Arguments `--stax_access_key` and `--stax_access_key_secret` required to run this program!")
