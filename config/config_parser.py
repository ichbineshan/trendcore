import os
import sys
import configargparse


root_dir = os.path.dirname(os.path.abspath(__file__))
default_config_files = "{0}/{1}".format(root_dir, "default.yaml")
print(default_config_files)



parser = configargparse.ArgParser(
    config_file_parser_class=configargparse.YAMLConfigFileParser,
    default_config_files=[default_config_files],
    auto_env_var_prefix="",
)

# Application


# Database
parser.add("--postgres_url", help="postgres_url")

# Redis
parser.add("--redis_url", help="redis_url")

# AI Models
parser.add("--openai_api_key", help="openai_api_key")

parser.add("--env", help="env")
parser.add("--port", type=int, help="port")
parser.add("--host", help="host")
parser.add("--mode", help="mode")
parser.add("--server_type", help="server_type")
parser.add("--realm", help="realm")
parser.add("--debug", help="debug", action="store_true")
parser.add("--postgres_nighteye_read_write", help="postgres_fynix_dofle_read_write")
parser.add("--mongo_night_eye_read_write", help="mongo_night_eye_read_write")
parser.add("--api_domain", help="api_domain")
parser.add("--redis_cerebrum_url", help="redis_cerebrum_url")
parser.add("--redis_fex_hiruzen_read_write", help="redis_fex_hiruzen_read_write")
parser.add("--storage_file_assets_private", help="storage_file_assets_private")
parser.add("--openai_gpt4_key", help="openai_gpt4_key")
parser.add("--google_genai_api_key", help="google_genai_api_key")
parser.add("--stream_token", help="stream_token")
parser.add("--clerk_secret_key", help="clerk_secret_key")
parser.add("--e2b_sandbox_api_key", help="e2b_sandbox_api_key")
parser.add("--anthropic_api_key", help="anthropic_api_key")
parser.add("--almanac_main_private_url", help="almanac_main_private_url")
parser.add("--firecrawl_api_key", help="firecrawl_api_key")
parser.add("--new_relic_app_name", help="new_relic_app_name")
parser.add("--new_relic_license_key", help="new_relic_license_key")
parser.add("--new_relic_monitor_mode", action="store_true", help="new_relic_monitor_mode")
parser.add("--new_relic_developer_mode", action="store_true", help="new_relic_developer_mode")
parser.add("--base_cdn_domain", help="base_cdn_domain")
parser.add("--locksmith_private_url", help="locksmith_private_url")
parser.add("--temporal_host", help="temporal_host")
parser.add("--temporal_namespace", help="temporal_namespace")
parser.add("--temporal_max_concurrent_activities", type=int, help="temporal_max_concurrent_activities")
parser.add("--embedding_model", help="embedding_model")
parser.add("--K8S_NODE_NAME", help="K8S_NODE_NAME")
parser.add("--K8S_POD_NAMESPACE", help="K8S_POD_NAMESPACE")
parser.add("--K8S_POD_NAME", help="K8S_POD_NAME")
parser.add("--sentry_environment", help="sentry_environment")
parser.add("--gcp_type", help="gcp_type")
parser.add("--gcp_project_id", help="gcp_project_id")
parser.add("--mcp_transport_type", help="mcp_transport_type")
parser.add("--number_of_candidate_images", help="number_of_candidate_images")
parser.add("--image_file_upload_subpath", help="image_file_upload_subpath")
parser.add("--elastic_search_url", help="elastic_search_url")
parser.add("--wgsn_edited_index_name", help="wgsn_edited_index_name")
parser.add("--serp_api_key", help="serp_api_key")
parser.add("--serp_base_url", help="serp_base_url")
parser.add("--fashion_general_index", help="fashion_general_index")
parser.add("--macro_trend_index", help="macro_trend_index")
parser.add("--micro_trend_index", help="micro_trend_index")
parser.add("--naruto_api_base_url", help="naruto_api_base_url")
parser.add("--naruto_webhook_base_url", help="naruto_webhook_base_url")
parser.add("--template_presentation_id", help="template_presentation_id")
parser.add("--shared_drive_id", help="shared_drive_id")
parser.add("--drive_n_slides_json_key", help="service account credentials json")


# Apify Configuration for Pinterest image scraping
parser.add("--apify_api_token", help="apify_api_token")
parser.add("--apify_pinterest_actor_id", help="apify_pinterest_actor_id")
parser.add("--pinterest_images_per_keyword", type=int, help="pinterest_images_per_keyword")
parser.add("--pinterest_images_refresh_days", type=int, help="pinterest_images_refresh_days")

# Ahrefs Configuration
parser.add("--ahrefs_api_key", help="ahrefs_api_key")
parser.add("--ahrefs_mcp_url", help="ahrefs_mcp_url")

arguments = sys.argv
print(arguments)
argument_options = parser.parse_known_args(arguments)
print(parser.format_values())
docker_args = argument_options[0]
