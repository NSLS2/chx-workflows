from tiled.client import from_profile
from prefect.blocks.system import Secret

import os

LOCATION="chx"

def get_tiled_client(structure_client=None):
    os.environ["TILED_API_KEY"] = Secret.load(f"tiled-{LOCATION}-api-key").get()
    if structure_client:
        tiled_client = from_profile("nsls2", structure_client=structure_client)[LOCATION]
    else:
        tiled_client = from_profile("nsls2")[LOCATION]
    os.environ.pop("TILED_API_KEY")
    return tiled_client
