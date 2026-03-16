from config.settings import loaded_config
from utils.cloud_storage import CloudStorageUtil
from utils.connection_manager import ConnectionManager


async def run_on_startup():
    try:
        await init_connections()
    except Exception as e:
        print(e)


async def run_on_exit():
    await loaded_config.connection_manager.close_connections()


async def init_connections():
    connection_manager = ConnectionManager(
        db_url=loaded_config.db_url, db_echo=loaded_config.db_echo
    )

    loaded_config.connection_manager = connection_manager
    try:
        loaded_config.cloud_storage_util = CloudStorageUtil(
            realm=loaded_config.realm,
            gcs_private_bucket_name=loaded_config.gcs_private_bucket_name
        )
    except Exception as e:
        print(e)

