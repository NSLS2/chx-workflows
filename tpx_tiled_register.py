import asyncio
from types import SimpleNamespace
from typing import Union

import numpy as np
from tiled.client import from_uri
from tiled.client.utils import ClientError
from tiled.adapters.parquet import ParquetDatasetAdapter
from tiled.utils import ensure_uri
from tiled.structures.table import TableStructure as table
from tiled.structures.data_source import DataSource, Management, Asset
from dataclasses import asdict
from pathlib import Path
import re
import dask.dataframe as dd
from tiled.client.register import create_node_or_drop_collision
from prefect import flow, get_run_logger, task



f_type = SimpleNamespace(
    HDF='.h5',
    PARQUET='.parquet')

def converted_path(filepath: Union[str, Path] , extension: str = f_type.PARQUET, cent: bool = False):
    """
    Converts .tpx3 file path(s) to corresponding output file path(s).
    Handles individual strings, Path objects, lists, or numpy arrays.

    This is specific to CHX beamline pre and post data security. Is there a better way or place to store this?

    Returns Path objects.
    """
    if isinstance(filepath, (list, np.ndarray)):
        return [converted_path(fp, extension = extension, cent = cent) for fp in filepath]

    filepath = Path(str(filepath).replace("file:", ""))

    if extension not in vars(f_type).values():
        raise TypeError(f"path conversion to unknown file type {extension}")

    str_filepath = str(filepath)
    if "/nsls2/data/chx/proposals/" in str_filepath:
        if "/assets/" in str_filepath:
            out_path = str(filepath).replace("/assets/", "/Compressed_Data/")
        elif "/manualassets/" in str_filepath:
            out_path = str(filepath).replace("/manualassets/", "/Compressed_Data/")
    else:
        #if not ("/nsls2/data/chx/legacy/" in str(filepath)):
            #warnings.warn(
            #    "unexpected file path used, operation will proceed but it is suggested to confirm correct target directory")
        out_path = str(filepath)
    # else:
    #     raise ValueError(f"Unknown path format: {filepath}")
    pre = ""
    if cent:
        pre = "_cent"
        
    return Path(out_path.replace(".tpx3", pre+extension))


@task(retries=1)
async def frame_register(client,paths,cent=True):
    logger = get_run_logger()
    logger.info()
    files = converted_path(paths, extension='.parquet', cent=cent)
    ddf = dd.read_parquet(files)
    system = [file.as_uri() for file in files]
    adapter = ParquetDatasetAdapter(system, table.from_dask_dataframe(ddf)).dataframe_adapter
    await create_node_or_drop_collision(client,
            key= "cent" if cent else "frame",
            structure_family=adapter.structure_family,
            metadata=dict(adapter.metadata()),
            specs=adapter.specs,
            data_sources=[
                DataSource(
                    structure_family=adapter.structure_family,
                    mimetype="application/x-parquet",
                    structure=asdict(adapter.structure()),
                    parameters={},
                    management=Management.external,
                    assets=[
                        Asset(
                            data_uri=ensure_uri(item),
                            is_directory=False,
                            parameter="data_uris",
                            num=i,
                        )
                        for i, item in enumerate(system)
                    ],
                )
            ],
        )
    

@flow(name="TPX Tiled Registration")
async def main():
    db = from_uri('https://tiled.nsls2.bnl.gov', 'dask')
    logger = get_run_logger()
    logger.info(db,type(db))
    raw = db['chx/raw']
    processed = db['chx/processed']

    sids = [*range(197192,197202),
            *range(197204,197209),
            *range(197313,197320),
            197364,197365,197366,
            *range(197368,197381),
            *range(197400,197406),
            *range(197444,197449),
            *range(197450,197455)]
    
    for sid in sids:
        client = raw[sid]
        logger.info(f"processing sid {sid}")
        try:
            target = processed.create_container(key=str(sid),metadata= dict(client.metadata))
        except ClientError as e:
            if 409 == e.response.status_code:
                logger.info(f"sid {sid} already has a processed container, it likely already has data, skipping")
            else:
                logger.info(f"unknown error {e} occurred with container generation, skipping")
            continue

        samples = client['primary/data/tpx3_files_raw_filepaths']
        for index in range(len(samples)):
            logger.info(f"\tprocessing sid sample {index} of {len(samples)}")
            fpaths = [re.sub(r'//[^/]+/', '/', str(f).replace('file:/media/nvme', '/nsls2/data/chx/proposals/2026-1')) for f in samples[index].compute()]
            try:
                tc = target.create_container(key=str(index))
            except ClientError:
                continue

            try:
                await frame_register(tc,fpaths,cent=True)
            except Exception as e:
                logger.info(f"attempting to register centroided data for sid {sid} failed with error: \n\t{e} \n... proceeding in attempting to register raw data")
            
            try:
                await frame_register(tc,fpaths,cent=False)
            except Exception as e:
                logger.info(f"attempting to register raw data for sid {sid} failed with error: \n\t{e}")


# if __name__ == "__main__":
#     asyncio.run(main())