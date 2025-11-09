from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    username: str
    password: str
    host: str
    port: int
    debug: bool
    root_dir: str

    model_config = SettingsConfigDict(env_prefix='DATA_SERVER_', env_file='.env')

__config = None

def get_config() -> Config:
    global __config
    if __config is None:
        __config = Config()
    return __config
