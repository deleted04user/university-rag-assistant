from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./university.db"
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    cors_origins: str = "http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:8080,http://localhost:8080,null"

    # Phase A — RAG local (Chroma + FastEmbed, sans API payante)
    rag_enabled: bool = True
    rag_index_path: str = "./rag_index.joblib"
    rag_top_k: int = 4
    # TF-IDF : seuil cosinus typique plus bas que les embeddings neuronaux.
    rag_min_similarity: float = 0.12


settings = Settings()
