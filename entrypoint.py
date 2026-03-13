import os

from config.settings import loaded_config

if loaded_config.env == "local":
    os.environ.setdefault('PKG_CONFIG_PATH', '/opt/homebrew/lib/pkgconfig:/opt/homebrew/opt/libffi/lib/pkgconfig')
    os.environ.setdefault('DYLD_LIBRARY_PATH', '/opt/homebrew/lib')
    os.environ.setdefault('LD_LIBRARY_PATH', '/opt/homebrew/lib')

if loaded_config.mode == "server":
    from app.main import main as server_main

    if __name__ == "__main__":
        server_main()
else:
    print(f"MODE '{loaded_config.mode}' not available")
    print("Available modes: server")
