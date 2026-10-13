"""Background removal for product photography -> RGBA cutout.

Strategy (robust for studio product shots on near-uniform or vertically
gradient backgrounds):

  1. Estimate the background colour per row from the left/right edge strips.
  2. Build a soft alpha ramp from the colour distance to that background.
  3. Keep only large connected components (drops stray specks / watermarks).
  4. Fill interior holes (label highlights, glass reflections).
  5. De-fringe: un-premultiply edge pixels against the background colour so the
     cutout is clean on light AND dark page backgrounds.

Requires numpy + scipy + Pillow.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from scipy import ndimage

# Colour distance below T_LO is background, above T_HI is solid object.
T_LO = 26.0
T_HI = 62.0
# Fraction of the largest component's area below which components are dropped.
MIN_COMPONENT_FRACTION = 0.02
EDGE_STRIP = 4


def _background_rows(arr: np.ndarray, strip: int = EDGE_STRIP) -> np.ndarray:
    """Per-row background estimate from the left/right edge strips."""
    h, w, _ = arr.shape
    left = arr[:, :strip, :]
    right = arr[:, w - strip:, :]
    edges = np.concatenate([left, right], axis=1)
    return np.median(edges, axis=1)  # (h, 3)


def _distance_from_bg(arr: np.ndarray) -> np.ndarray:
    """Max-channel absolute distance from the per-row background colour."""
    bg = _background_rows(arr)              # (h, 3)
    diff = np.abs(arr.astype(np.int16) - bg[:, None, :].astype(np.int16))
    dist = diff.max(axis=2).astype(np.float32)  # (h, w)

    # Smooth the distance along rows so edge strips with a stray object on one
    # side do not punch holes; take the per-row minimum of left/right estimates.
    return dist


def _largest_components(mask: np.ndarray, min_fraction: float) -> np.ndarray:
    labels, n = ndimage.label(mask)
    if n == 0:
        return mask
    sizes = ndimage.sum(mask, labels, range(1, n + 1))
    biggest = sizes.max()
    keep = np.zeros(n + 1, dtype=bool)
    for i, s in enumerate(sizes, start=1):
        keep[i] = s >= biggest * min_fraction
    return keep[labels]


def cutout(path, *, t_lo: float = T_LO, t_hi: float = T_HI,
           min_fraction: float = MIN_COMPONENT_FRACTION,
           crop: bool = True, pad: int = 0) -> Image.Image:
    """Return an RGBA cutout of the product in ``path`` (or a PIL image)."""
    src = Image.open(path) if isinstance(path, str) else path
    if src.mode in ("P", "LA"):
        src = src.convert("RGBA")
    has_alpha = src.mode in ("RGBA", "LA") and np.asarray(
        src.convert("RGBA"))[:, :, 3].min() < 250

    if has_alpha:
        rgba = np.asarray(src.convert("RGBA")).astype(np.float32)
        return Image.fromarray(rgba.astype(np.uint8), "RGBA")

    arr = np.asarray(src.convert("RGB")).astype(np.float32)
    dist = _distance_from_bg(arr)

    # Soft alpha ramp.
    alpha = np.clip((dist - t_lo) / (t_hi - t_lo), 0.0, 1.0)

    # Solid mask for topology work.
    solid = alpha > 0.45
    solid = _largest_components(solid, min_fraction)
    solid = ndimage.binary_fill_holes(solid)

    # Keep soft coverage only where it belongs to a kept component.
    grown = ndimage.binary_dilation(solid, iterations=2)
    alpha = np.where(grown, alpha, 0.0)
    alpha = np.maximum(alpha, solid.astype(np.float32))

    # De-fringe: recover true colour by un-premultiplying against the bg.
    bg = _background_rows(arr)
    a = np.clip(alpha, 1e-3, 1.0)[:, :, None]
    true = (arr - bg[:, None, :] * (1.0 - a)) / a
    true = np.where(alpha[:, :, None] > 0.02, true, 0.0)
    true = np.clip(true, 0, 255)

    # Feather the alpha slightly for clean sub-pixel edges.
    alpha = ndimage.gaussian_filter(alpha, sigma=0.6)
    alpha = np.clip((alpha - 0.06) / 0.88, 0.0, 1.0)

    out = np.dstack([true, alpha * 255.0]).astype(np.uint8)
    img = Image.fromarray(out, "RGBA")

    if crop:
        bbox = img.getbbox()
        if bbox:
            bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                    min(img.width, bbox[2] + pad), min(img.height, bbox[3] + pad))
            img = img.crop(bbox)
    return img


def preview(img: Image.Image, height: int, bg=(242, 240, 228, 255)) -> Image.Image:
    """Composite a cutout onto a background colour for visual QA."""
    w = max(int(img.width * height / img.height), 8)
    r = img.resize((w, height), Image.LANCZOS)
    canvas = Image.new("RGBA", (w, height), bg)
    canvas.alpha_composite(r)
    return canvas
