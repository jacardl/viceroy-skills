"""9Router image generation backend.

Exposes 9Router's image generation models (cx/gpt-5.5-image, etc.)
via the local 9Router gateway (http://127.0.0.1:20128/v1)
as an :class:`ImageGenProvider` implementation.

Selection precedence (first hit wins):

1. ``image_gen.model`` in ``config.yaml``  (e.g. ``cx/gpt-5.5-image``)
2. :data:`DEFAULT_MODEL` — ``cx/gpt-5.5-image``
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import requests

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    resolve_aspect_ratio,
    save_b64_image,
    save_url_image,
    success_response,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model catalog
# ---------------------------------------------------------------------------

_MODELS: Dict[str, Dict[str, Any]] = {
    "cx/gpt-5.5-image": {
        "display": "GPT-5.5 Image (via 9Router)",
        "speed": "~99s",
        "strengths": "Highest quality GPT-5.5 image model via local 9Router gateway",
    },
    "cx/gpt-5.4-image": {
        "display": "GPT-5.4 Image (via 9Router)",
        "speed": "~90s",
        "strengths": "GPT-5.4 image model via local 9Router gateway",
    },
    "cx/gpt-5.3-image": {
        "display": "GPT-5.3 Image (via 9Router)",
        "speed": "~80s",
        "strengths": "GPT-5.3 image model via local 9Router gateway",
    },
}

DEFAULT_MODEL = "cx/gpt-5.5-image"

# OpenAI-compatible size format
_SIZE_MAP = {
    "landscape": "1792x1024",
    "square": "1024x1024",
    "portrait": "1024x1792",
}

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _load_9router_config() -> Dict[str, Any]:
    """Read ``providers.9router`` from config.yaml (returns {} on any failure)."""
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        if not isinstance(cfg, dict):
            return {}
        providers = cfg.get("providers", {})
        if not isinstance(providers, dict):
            return {}
        return providers.get("9router", {}) or {}
    except Exception as exc:
        logger.debug("Could not load providers.9router config: %s", exc)
        return {}


def _load_image_gen_config() -> Dict[str, Any]:
    """Read ``image_gen`` from config.yaml (returns {} on any failure)."""
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        if not isinstance(cfg, dict):
            return {}
        section = cfg.get("image_gen", {})
        return section if isinstance(section, dict) else {}
    except Exception as exc:
        logger.debug("Could not load image_gen config: %s", exc)
        return {}


def _resolve_model() -> str:
    """Return the model id to use, preferring image_gen.model then DEFAULT_MODEL."""
    cfg = _load_image_gen_config()
    model = cfg.get("model")
    if isinstance(model, str) and model.strip():
        return model.strip()
    return DEFAULT_MODEL


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

class NineRouterImageGenProvider(ImageGenProvider):
    """9Router ``/v1/images/generations`` backend — OpenAI-compatible."""

    @property
    def name(self) -> str:
        return "9router"

    @property
    def display_name(self) -> str:
        return "9Router"

    def is_available(self) -> bool:
        cfg = _load_9router_config()
        api = cfg.get("api", "").strip()
        key = cfg.get("api_key", "").strip()
        return bool(api and key)

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": model_id,
                "display": meta["display"],
                "speed": meta["speed"],
                "strengths": meta["strengths"],
                "price": "varies",
            }
            for model_id, meta in _MODELS.items()
        ]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "9Router",
            "badge": "local",
            "tag": "Local 9Router gateway — /v1/images/generations (cx/gpt-5.5-image etc.)",
            "env_vars": [],
        }

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        prompt_text = (prompt or "").strip()
        aspect = resolve_aspect_ratio(aspect_ratio)
        model_id = _resolve_model()

        if not prompt_text:
            return error_response(
                error="Prompt is required and must be a non-empty string",
                error_type="invalid_argument",
                provider="9router",
                aspect_ratio=aspect,
            )

        cfg = _load_9router_config()
        base_url = cfg.get("api", "").strip().rstrip("/")
        api_key = cfg.get("api_key", "").strip()

        if not base_url or not api_key:
            return error_response(
                error=(
                    "9Router provider not configured. Set providers.9router.api "
                    "and providers.9router.api_key in config.yaml, or run "
                    "`hermes setup` → Image Generation → 9Router."
                ),
                error_type="missing_api_key",
                provider="9router",
                model=model_id,
                aspect_ratio=aspect,
            )

        size = _SIZE_MAP.get(aspect, _SIZE_MAP["square"])

        payload: Dict[str, Any] = {
            "model": model_id,
            "prompt": prompt_text,
            "n": 1,
            "size": size,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                f"{base_url}/images/generations",
                headers=headers,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            err_msg = str(exc)
            if exc.response is not None:
                try:
                    err_data = exc.response.json()
                    if isinstance(err_data, dict):
                        err_msg = (
                            err_data.get("error", {}).get("message")
                            or str(err_data.get("error", err_data))
                            or str(exc)
                        )
                except Exception:
                    pass
            logger.error("9Router image gen failed (%d): %s", status, err_msg)
            return error_response(
                error=f"9Router image generation failed ({status}): {err_msg}",
                error_type="api_error",
                provider="9router",
                model=model_id,
                prompt=prompt_text,
                aspect_ratio=aspect,
            )
        except requests.RequestException as exc:
            logger.error("9Router image gen network error: %s", exc)
            return error_response(
                error=f"9Router network error: {exc}",
                error_type="network_error",
                provider="9router",
                model=model_id,
                prompt=prompt_text,
                aspect_ratio=aspect,
            )

        try:
            data = response.json()
        except Exception as exc:
            return error_response(
                error=f"Could not parse 9Router response: {exc}",
                error_type="parse_error",
                provider="9router",
                model=model_id,
                prompt=prompt_text,
                aspect_ratio=aspect,
            )

        images = data.get("data", []) if isinstance(data, dict) else []
        first = images[0] if images else {}

        image_ref: Optional[str] = None

        b64 = first.get("b64_json")
        if b64:
            try:
                path = save_b64_image(b64, prefix="9router_image")
                image_ref = str(path)
            except Exception as exc:
                return error_response(
                    error=f"Could not save image to cache: {exc}",
                    error_type="io_error",
                    provider="9router",
                    model=model_id,
                    prompt=prompt_text,
                    aspect_ratio=aspect,
                )

        url = first.get("url")
        if url and not image_ref:
            try:
                path = save_url_image(url, prefix="9router_image")
                image_ref = str(path)
            except Exception as exc:
                logger.warning("9Router image URL could not be cached (%s); using bare URL.", exc)
                image_ref = url

        if not image_ref:
            return error_response(
                error="9Router returned no image data",
                error_type="empty_response",
                provider="9router",
                model=model_id,
                prompt=prompt_text,
                aspect_ratio=aspect,
            )

        return success_response(
            image=image_ref,
            model=model_id,
            prompt=prompt_text,
            aspect_ratio=aspect,
            provider="9router",
            extra={"size": size},
        )


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    """Plugin entry point — wire ``NineRouterImageGenProvider`` into the registry."""
    ctx.register_image_gen_provider(NineRouterImageGenProvider())
