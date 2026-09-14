/**
 * Base URL de l'API FastAPI (sans slash final).
 * Sous Windows, le port 8000 est souvent bloqué (WinError 10013) : utiliser 8001.
 */
window.API_BASE = window.API_BASE || "http://127.0.0.1:8001";
