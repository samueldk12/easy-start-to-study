"""
Encrypted Credentials Vault for StackStudio.

Stores generic and cloud-provider credentials encrypted at rest with a key derived
(PBKDF2-HMAC-SHA256) from a master password. The derived key only ever lives in
process memory (never persisted to disk) -- the vault must be unlocked again with
the master password every time the StackStudio server process is (re)started.
"""

import os
import json
import base64
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
VAULT_FILE = os.path.join(DATA_DIR, "credentials.vault.json")

_KDF_ITERATIONS = 390_000
_VERIFIER_PLAINTEXT = b"stackstudio-vault-check-v1"

# Describes which secret fields each credential type expects, and (when applicable)
# how those fields map onto environment variables / files when a credential is
# "applied" to a project's .env for local cloud/service integration.
PROVIDER_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "generic": {
        "label": "Genérica (chave/valor)",
        "freeform": True,
        "fields": [],
        "env_map": {}
    },
    "aws": {
        "label": "AWS (Amazon Web Services)",
        "fields": [
            {"key": "aws_access_key_id", "label": "Access Key ID", "secret": False},
            {"key": "aws_secret_access_key", "label": "Secret Access Key", "secret": True},
            {"key": "aws_session_token", "label": "Session Token (opcional)", "secret": True, "optional": True},
            {"key": "region", "label": "Região (ex: us-east-1)", "secret": False, "optional": True},
        ],
        "env_map": {
            "aws_access_key_id": "AWS_ACCESS_KEY_ID",
            "aws_secret_access_key": "AWS_SECRET_ACCESS_KEY",
            "aws_session_token": "AWS_SESSION_TOKEN",
            "region": "AWS_DEFAULT_REGION",
        }
    },
    "gcp": {
        "label": "Google Cloud Platform",
        "fields": [
            {"key": "project_id", "label": "Project ID", "secret": False},
            {"key": "service_account_json", "label": "Conteúdo do Service Account (JSON)", "secret": True, "multiline": True},
        ],
        "env_map": {
            "project_id": "GOOGLE_CLOUD_PROJECT",
        },
        "file_field": "service_account_json",
        "file_name": "gcp-service-account.json",
        "file_env": "GOOGLE_APPLICATION_CREDENTIALS"
    },
    "azure": {
        "label": "Microsoft Azure",
        "fields": [
            {"key": "tenant_id", "label": "Tenant ID", "secret": False},
            {"key": "client_id", "label": "Client ID", "secret": False},
            {"key": "client_secret", "label": "Client Secret", "secret": True},
            {"key": "subscription_id", "label": "Subscription ID", "secret": False, "optional": True},
        ],
        "env_map": {
            "tenant_id": "AZURE_TENANT_ID",
            "client_id": "AZURE_CLIENT_ID",
            "client_secret": "AZURE_CLIENT_SECRET",
            "subscription_id": "AZURE_SUBSCRIPTION_ID",
        }
    },
    "docker_registry": {
        "label": "Docker Registry Privado",
        "fields": [
            {"key": "registry", "label": "Registry (ex: registry.exemplo.com)", "secret": False},
            {"key": "username", "label": "Usuário", "secret": False},
            {"key": "password", "label": "Senha / Token", "secret": True},
        ],
        "env_map": {
            "registry": "DOCKER_REGISTRY",
            "username": "DOCKER_REGISTRY_USER",
            "password": "DOCKER_REGISTRY_PASSWORD",
        }
    },
    "database": {
        "label": "Banco de Dados",
        "fields": [
            {"key": "host", "label": "Host", "secret": False},
            {"key": "port", "label": "Porta", "secret": False, "optional": True},
            {"key": "user", "label": "Usuário", "secret": False},
            {"key": "password", "label": "Senha", "secret": True},
            {"key": "database", "label": "Nome do Banco", "secret": False, "optional": True},
        ],
        "env_map": {
            "host": "DB_HOST",
            "port": "DB_PORT",
            "user": "DB_USER",
            "password": "DB_PASSWORD",
            "database": "DB_NAME",
        }
    },
    "api_key": {
        "label": "API Key Genérica",
        "fields": [
            {"key": "key", "label": "Chave da API", "secret": True},
        ],
        "env_map": {
            "key": "API_KEY",
        }
    },
    "ssh_key": {
        "label": "Chave SSH",
        "fields": [
            {"key": "private_key", "label": "Chave Privada", "secret": True, "multiline": True},
            {"key": "passphrase", "label": "Passphrase (opcional)", "secret": True, "optional": True},
        ],
        "env_map": {
            "passphrase": "SSH_KEY_PASSPHRASE",
        },
        "file_field": "private_key",
        "file_name": "id_rsa",
        "file_env": "SSH_PRIVATE_KEY_PATH"
    },
}


class VaultLockedError(Exception):
    pass


class VaultNotInitializedError(Exception):
    pass


class InvalidPasswordError(Exception):
    pass


class _VaultSession:
    """Process-local, never-persisted holder for the unlocked Fernet key."""

    def __init__(self):
        self._lock = threading.Lock()
        self._fernet: Optional[Fernet] = None
        self._unlocked_at: Optional[str] = None

    def set(self, fernet: Fernet):
        with self._lock:
            self._fernet = fernet
            self._unlocked_at = datetime.now().isoformat()

    def clear(self):
        with self._lock:
            self._fernet = None
            self._unlocked_at = None

    def get(self) -> Optional[Fernet]:
        with self._lock:
            return self._fernet

    @property
    def unlocked_at(self) -> Optional[str]:
        with self._lock:
            return self._unlocked_at


_session = _VaultSession()


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=_KDF_ITERATIONS)
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


class CredentialVault:
    @staticmethod
    def _ensure_data_dir():
        os.makedirs(DATA_DIR, exist_ok=True)

    @staticmethod
    def _load_raw() -> Dict[str, Any]:
        if not os.path.exists(VAULT_FILE):
            return {}
        try:
            with open(VAULT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def _save_raw(data: Dict[str, Any]):
        CredentialVault._ensure_data_dir()
        temp_file = VAULT_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        if os.path.exists(VAULT_FILE):
            os.replace(temp_file, VAULT_FILE)
        else:
            os.rename(temp_file, VAULT_FILE)

    @staticmethod
    def is_initialized() -> bool:
        raw = CredentialVault._load_raw()
        return bool(raw.get("salt") and raw.get("verifier"))

    @staticmethod
    def is_unlocked() -> bool:
        return _session.get() is not None

    @staticmethod
    def status() -> Dict[str, Any]:
        return {
            "initialized": CredentialVault.is_initialized(),
            "unlocked": CredentialVault.is_unlocked(),
            "unlocked_at": _session.unlocked_at,
            "credential_count": len(CredentialVault._load_raw().get("credentials", {}))
        }

    @staticmethod
    def setup(password: str) -> Dict[str, Any]:
        if CredentialVault.is_initialized():
            raise ValueError("O cofre já foi inicializado. Use a opção de desbloqueio.")
        if not password or len(password) < 8:
            raise ValueError("A senha mestra deve ter pelo menos 8 caracteres.")

        salt = os.urandom(16)
        fernet = Fernet(_derive_key(password, salt))
        verifier = fernet.encrypt(_VERIFIER_PLAINTEXT).decode("utf-8")

        raw = {
            "version": 1,
            "kdf": "pbkdf2_sha256",
            "iterations": _KDF_ITERATIONS,
            "salt": base64.b64encode(salt).decode("utf-8"),
            "verifier": verifier,
            "credentials": {}
        }
        CredentialVault._save_raw(raw)
        _session.set(fernet)
        return CredentialVault.status()

    @staticmethod
    def unlock(password: str) -> Dict[str, Any]:
        raw = CredentialVault._load_raw()
        if not raw.get("salt") or not raw.get("verifier"):
            raise VaultNotInitializedError("O cofre ainda não foi configurado. Defina uma senha mestra primeiro.")

        salt = base64.b64decode(raw["salt"])
        fernet = Fernet(_derive_key(password, salt))
        try:
            plaintext = fernet.decrypt(raw["verifier"].encode("utf-8"))
        except InvalidToken:
            raise InvalidPasswordError("Senha mestra incorreta.")

        if plaintext != _VERIFIER_PLAINTEXT:
            raise InvalidPasswordError("Senha mestra incorreta.")

        _session.set(fernet)
        return CredentialVault.status()

    @staticmethod
    def lock():
        _session.clear()

    @staticmethod
    def change_password(old_password: str, new_password: str) -> Dict[str, Any]:
        if not new_password or len(new_password) < 8:
            raise ValueError("A nova senha mestra deve ter pelo menos 8 caracteres.")

        # Validates old_password against the current salt/verifier and unlocks with it
        CredentialVault.unlock(old_password)
        old_fernet = _session.get()

        raw = CredentialVault._load_raw()
        decrypted_entries = {}
        for cid, entry in raw.get("credentials", {}).items():
            ciphertext = entry.get("ciphertext")
            decrypted_entries[cid] = json.loads(old_fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")) if ciphertext else {}

        new_salt = os.urandom(16)
        new_fernet = Fernet(_derive_key(new_password, new_salt))

        for cid, entry in raw.get("credentials", {}).items():
            entry["ciphertext"] = new_fernet.encrypt(json.dumps(decrypted_entries[cid]).encode("utf-8")).decode("utf-8")
            entry["updated_at"] = datetime.now().isoformat()

        raw["salt"] = base64.b64encode(new_salt).decode("utf-8")
        raw["verifier"] = new_fernet.encrypt(_VERIFIER_PLAINTEXT).decode("utf-8")
        CredentialVault._save_raw(raw)
        _session.set(new_fernet)
        return CredentialVault.status()

    @staticmethod
    def get_providers() -> Dict[str, Any]:
        return PROVIDER_SCHEMAS

    @staticmethod
    def list_credentials() -> List[Dict[str, Any]]:
        raw = CredentialVault._load_raw()
        result = []
        for cid, entry in raw.get("credentials", {}).items():
            result.append({
                "id": cid,
                "name": entry.get("name"),
                "type": entry.get("type"),
                "notes": entry.get("notes", ""),
                "created_at": entry.get("created_at"),
                "updated_at": entry.get("updated_at"),
                "field_keys": list(entry.get("field_keys", []))
            })
        return sorted(result, key=lambda x: x.get("created_at") or "", reverse=True)

    @staticmethod
    def _require_unlocked() -> Fernet:
        fernet = _session.get()
        if fernet is None:
            raise VaultLockedError("O cofre está bloqueado. Desbloqueie com a senha mestra primeiro.")
        return fernet

    @staticmethod
    def create_credential(name: str, cred_type: str, data: Dict[str, str], notes: str = "") -> Dict[str, Any]:
        fernet = CredentialVault._require_unlocked()
        if not name or not name.strip():
            raise ValueError("Nome da credencial é obrigatório.")
        if cred_type not in PROVIDER_SCHEMAS:
            raise ValueError(f"Tipo de credencial desconhecido: {cred_type}")

        raw = CredentialVault._load_raw()
        cid = uuid.uuid4().hex[:12]
        now = datetime.now().isoformat()
        ciphertext = fernet.encrypt(json.dumps(data or {}).encode("utf-8")).decode("utf-8")

        raw.setdefault("credentials", {})[cid] = {
            "id": cid,
            "name": name.strip(),
            "type": cred_type,
            "notes": notes or "",
            "created_at": now,
            "updated_at": now,
            "field_keys": list((data or {}).keys()),
            "ciphertext": ciphertext
        }
        CredentialVault._save_raw(raw)
        return CredentialVault.get_credential_meta(cid)

    @staticmethod
    def get_credential_meta(cid: str) -> Optional[Dict[str, Any]]:
        for c in CredentialVault.list_credentials():
            if c["id"] == cid:
                return c
        return None

    @staticmethod
    def update_credential(cid: str, name: Optional[str] = None, data: Optional[Dict[str, str]] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        fernet = CredentialVault._require_unlocked()
        raw = CredentialVault._load_raw()
        entry = raw.get("credentials", {}).get(cid)
        if not entry:
            raise KeyError(f"Credencial '{cid}' não encontrada.")

        if name is not None and name.strip():
            entry["name"] = name.strip()
        if notes is not None:
            entry["notes"] = notes
        if data is not None:
            entry["ciphertext"] = fernet.encrypt(json.dumps(data).encode("utf-8")).decode("utf-8")
            entry["field_keys"] = list(data.keys())
        entry["updated_at"] = datetime.now().isoformat()

        raw["credentials"][cid] = entry
        CredentialVault._save_raw(raw)
        return CredentialVault.get_credential_meta(cid)

    @staticmethod
    def delete_credential(cid: str) -> bool:
        CredentialVault._require_unlocked()
        raw = CredentialVault._load_raw()
        if cid in raw.get("credentials", {}):
            del raw["credentials"][cid]
            CredentialVault._save_raw(raw)
            return True
        return False

    @staticmethod
    def reveal_credential(cid: str) -> Dict[str, Any]:
        fernet = CredentialVault._require_unlocked()
        raw = CredentialVault._load_raw()
        entry = raw.get("credentials", {}).get(cid)
        if not entry:
            raise KeyError(f"Credencial '{cid}' não encontrada.")
        data = json.loads(fernet.decrypt(entry["ciphertext"].encode("utf-8")).decode("utf-8"))
        return {
            "id": cid,
            "name": entry.get("name"),
            "type": entry.get("type"),
            "notes": entry.get("notes", ""),
            "data": data
        }

    @staticmethod
    def apply_to_project(cid: str, project_path: str) -> Dict[str, Any]:
        """
        Decrypts a stored credential and writes it into the target project's .env file
        (creating/merging as needed), following the env-var mapping / file conventions
        of its provider type. Secrets touch disk here in plaintext, same as any local
        .env-based workflow -- the project's .env (and any .secrets/ folder created
        here) must stay out of version control.
        """
        revealed = CredentialVault.reveal_credential(cid)
        cred_type = revealed["type"]
        data = revealed["data"]
        schema = PROVIDER_SCHEMAS.get(cred_type, PROVIDER_SCHEMAS["generic"])

        env_updates: Dict[str, str] = {}

        if schema.get("freeform"):
            for k, v in data.items():
                env_updates[k.strip().upper().replace(" ", "_").replace("-", "_")] = str(v)
        else:
            for field_key, env_name in schema.get("env_map", {}).items():
                if data.get(field_key):
                    env_updates[env_name] = str(data[field_key])

        # Providers whose secret is a blob (service-account JSON, private key) get
        # written to a dedicated, gitignored folder inside the project instead of .env.
        file_field = schema.get("file_field")
        if file_field and data.get(file_field):
            secrets_dir = os.path.join(project_path, ".secrets")
            os.makedirs(secrets_dir, exist_ok=True)
            gitignore_path = os.path.join(secrets_dir, ".gitignore")
            if not os.path.exists(gitignore_path):
                with open(gitignore_path, "w", encoding="utf-8") as f:
                    f.write("*\n!.gitignore\n")

            file_name = schema.get("file_name", f"{cid}.secret")
            file_path = os.path.join(secrets_dir, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(data[file_field])
            try:
                os.chmod(file_path, 0o600)
            except Exception:
                pass
            env_updates[schema.get("file_env", "CREDENTIAL_FILE_PATH")] = file_path

        if not env_updates:
            raise ValueError("Esta credencial não possui campos para aplicar como variáveis de ambiente.")

        CredentialVault._merge_env_file(project_path, env_updates)
        return {"applied_vars": list(env_updates.keys()), "project_path": project_path}

    @staticmethod
    def _merge_env_file(project_path: str, updates: Dict[str, str]):
        env_path = os.path.join(project_path, ".env")
        lines: List[str] = []
        replaced = set()

        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                lines[i] = f"{key}={updates[key]}"
                replaced.add(key)

        new_keys = [k for k in updates if k not in replaced]
        if new_keys:
            if lines:
                lines.append("")
            lines.append(f"# Credenciais aplicadas via Cofre do StackStudio em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            for key in new_keys:
                lines.append(f"{key}={updates[key]}")

        os.makedirs(project_path, exist_ok=True)
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
