from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file=".env",extra="ignore")
    database_url:str="sqlite:///./dropverse.sqlite3"
    bot_token:str=""
    app_base_url:str="http://localhost:5173"
    admin_telegram_ids:str=""
    environment:str="development"
    telegram_init_data_max_age:int=86400
    cors_origins:str="http://localhost:5173"
    @property
    def admin_ids(self):
        return {int(x.strip()) for x in self.admin_telegram_ids.split(',') if x.strip().isdigit()}
    @property
    def cors_list(self):
        return [x.strip() for x in self.cors_origins.split(',') if x.strip()]
settings=Settings()
