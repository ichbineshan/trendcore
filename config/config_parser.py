import os
import sys
import configargparse

root_dir = os.path.dirname(os.path.abspath(__file__))
default_config_files = f"{root_dir}/default.yaml"

parser = configargparse.ArgParser(
    config_file_parser_class=configargparse.YAMLConfigFileParser,
    default_config_files=[default_config_files],
    auto_env_var_prefix="",
)

# Application
parser.add("--env", help="env")
parser.add("--port", help="port")
parser.add("--host", help="host")
parser.add("--mode", help="mode")
parser.add("--debug", help="debug", action="store_true")

# Database
parser.add("--postgres_url", help="postgres_url")

# Redis
parser.add("--redis_url", help="redis_url")

# AI Models
parser.add("--openai_api_key", help="openai_api_key")

arguments = sys.argv
argument_options = parser.parse_known_args(arguments)
docker_args = argument_options[0]
