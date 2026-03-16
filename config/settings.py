import enum
import os
from typing import Optional, Set

#from clerk_integration.utils import ClerkAuthHelper
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.config_parser import docker_args
from utils.cloud_storage import CloudStorageUtil
from utils.connection_manager import ConnectionManager
from utils.sqlalchemy import async_db_url

args = docker_args


class LogLevel(enum.Enum):  # noqa: WPS600
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class AnalyticsConfig(BaseModel):
    measurement_id: str
    secret_key: str


class GCPConfig(BaseModel):
    type: str
    project_id: str


class VSCodeConfig(BaseModel):
    analytics: AnalyticsConfig
    gcp: GCPConfig
    sentry_dsn: str


class Settings(BaseSettings):
    # pydantic v2: use model_config with SettingsConfigDict to define settings configuration
    model_config = SettingsConfigDict()

    env: str = args.env
    port: int = args.port
    host: str = args.host
    debug: bool = args.debug
    workers_count: int = 1
    mode: str = args.mode
    db_url: str = async_db_url(args.postgres_nighteye_read_write)
    redis_cerebrum_url: str = os.getenv(
        "REDIS_FEX_NEJI_READ_WRITE", args.redis_cerebrum_url
    )
    db_echo: bool = args.debug
    server_type: str = args.server_type
    realm: str = args.realm
    gcs_private_bucket_name: str = args.storage_file_assets_private.removeprefix("gs://")
    log_level: str = LogLevel.INFO.value

    # svc to call internal services
    api_domain: str = args.api_domain
    fex_ingestion_url: str = args.api_domain + (
        "/service/ingestion" if args.env != "local" else ""
    )

    openai_gpt4_key: str = os.getenv("OPENAI_KEY1", args.openai_gpt4_key)
    google_genai_api_key: str = args.google_genai_api_key

    # global class instances
    connection_manager: Optional[ConnectionManager] = None
    connection_manager_locksmith: Optional[ConnectionManager] = None
    read_connection_manager: Optional[ConnectionManager] = None
    cloud_storage_util: Optional[CloudStorageUtil] = None
    temporal_host: str = args.temporal_host
    temporal_namespace: str = args.temporal_namespace or "default"
    temporal_max_concurrent_activities: int = args.temporal_max_concurrent_activities or 10

    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    POD_NAMESPACE: str = args.K8S_POD_NAMESPACE
    NODE_NAME: str = args.K8S_NODE_NAME
    POD_NAME: str = args.K8S_POD_NAME

    sentry_dsn: Optional[str] = os.getenv("SENTRY_DSN")
    sentry_sample_rate: float = 1.0
    sentry_environment: str = args.sentry_environment

    ws_connections: Optional[Set] = None

    clerk_secret_key: str = args.clerk_secret_key
    # clerk_auth_helper: ClerkAuthHelper = ClerkAuthHelper(
    #     service_name="night_eye", clerk_secret_key=clerk_secret_key
    # )
    e2b_sandbox_api_key: str = args.e2b_sandbox_api_key
    stream_token: Optional[str] = args.stream_token
    memory_index: str = "memory_index"
    anthropic_api_key: str = args.anthropic_api_key
    almanac_main_private_url: str = args.almanac_main_private_url

    # GCP configuration values
    gcp_type: str = args.gcp_type
    gcp_project_id: str = args.gcp_project_id
    gcp: GCPConfig = GCPConfig(type=gcp_type, project_id=gcp_project_id)

    logging_config: dict = {
        "log_level": "INFO",
        "sentry_dsn": sentry_dsn,
        "sentry_environment": sentry_environment,
        "sentry_release": None,  # Or add version "1.0.0"
        "enable_console_output": True,  # toggle console/terminal printing
        "enable_json_output": True,  # Toggle between json and line format,
        "custom_processors": [],  # add custom log processors to add additional details like service name, timestamp etc. Pass function object
    }

    firecrawl_api_key: str = args.firecrawl_api_key

    # New Relic Configuration
    new_relic_app_name: Optional[str] = args.new_relic_app_name
    new_relic_license_key: Optional[str] = args.new_relic_license_key
    new_relic_monitor_mode: Optional[bool] = args.new_relic_monitor_mode
    new_relic_developer_mode: Optional[bool] = args.new_relic_developer_mode
    base_cdn_domain: str = args.base_cdn_domain
    locksmith_private_url: str = args.locksmith_private_url
    redis_fex_hiruzen_read_write: str = args.redis_fex_hiruzen_read_write
    embedding_model: Optional[str] = args.embedding_model
    mcp_transport_type: Optional[str] = args.mcp_transport_type
    number_of_candidate_images: Optional[int] = args.number_of_candidate_images or 1
    image_file_upload_subpath:Optional[str] = args.image_file_upload_subpath
    serp_api_key: Optional[str] = args.serp_api_key
    serp_base_url: Optional[str] = args.serp_base_url
    elastic_search_url: Optional[str] = args.elastic_search_url
    wgsn_edited_index_name: Optional[str] = args.wgsn_edited_index_name
    fashion_general_index: Optional[str] = args.fashion_general_index
    macro_trend_index: Optional[str] = args.macro_trend_index
    micro_trend_index: Optional[str] = args.micro_trend_index
    mongo_night_eye_read_write: Optional[str] = args.mongo_night_eye_read_write

    # Apify Configuration for Pinterest image scraping
    apify_api_token: Optional[str] = args.apify_api_token
    apify_pinterest_actor_id: Optional[str] = args.apify_pinterest_actor_id or "apify~pinterest-crawler"
    pinterest_images_per_keyword: int = args.pinterest_images_per_keyword or 5
    pinterest_images_refresh_days: int = args.pinterest_images_refresh_days or 7
    naruto_api_base_url: Optional[str] = args.naruto_api_base_url or "https://api.create.sit.fyndx1.de"
    naruto_webhook_base_url: Optional[str] = args.naruto_webhook_base_url or ""

    # Ahrefs Configuration
    ahrefs_api_key: Optional[str] = args.ahrefs_api_key
    ahrefs_mcp_url: str = args.ahrefs_mcp_url or "https://api.ahrefs.com/mcp/mcp"
    template_presentation_id: Optional[str] = args.template_presentation_id or "1QgqUf-Kh0-Lvn9GWxRe_H36ZlWF3fGTl_tXwKP9lT3E"
    shared_drive_id: Optional[str] = args.shared_drive_id or "0APiX8kPWI52xUk9PVA"
    drive_n_slides_json_key: str = os.getenv("DRIVE_N_SLIDES_JSON_KEY", args.openai_gpt4_key)





loaded_config = Settings()
