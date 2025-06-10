# tests/docker_utils.py
"""
Utility helpers for Docker-based tests or local experimentation.
"""

from pathlib import Path
from typing import Optional

from docker import from_env as docker_from_env
from docker.errors import ImageNotFound

DEFAULT_TAG = "cadet-api"


def build_cadet_image(
    *,
    tag: str = DEFAULT_TAG,
    context_dir: Optional[Path] = None,
    dockerfile: str = "Dockerfile_ubuntu",
    rebuild: bool = False,
):
    """
    Build (or fetch, if it already exists) the CADet-API Docker image.

    Args:
        tag:       Name:tag for the resulting image.
        context_dir: Build context dir; defaults to project root.
        dockerfile:  Dockerfile path relative to context_dir.
        rebuild:     If False and an image with *tag* already exists, reuse it.

    Returns:
        docker.models.images.Image
    """
    client = docker_from_env()
    client.ping()

    if not rebuild:
        try:
            return client.images.get(tag)
        except ImageNotFound:
            pass  # fall through and build

    ctx = context_dir or Path(__file__).resolve().parents[1]
    print(f"Building image {tag!r} from {ctx}/{dockerfile}")
    image, _ = client.images.build(
        path=str(ctx),
        dockerfile=dockerfile,
        tag=tag,
        rm=True,
    )
    return image
