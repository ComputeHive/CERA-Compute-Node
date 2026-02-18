from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_NAME:str = "CERA_VM Manager"
    VERSION:str = '1.0.0'
    APP_STATE_DIR:str = "/var/lib/"