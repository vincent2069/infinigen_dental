# Copyright (C) 2024, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory of this source tree.

# Authors:
# - Karhan Kayan

import os
import random
from pathlib import Path

import bpy
import numpy as np

from infinigen.assets.utils.bbox_from_mesh import box_from_corners
from infinigen.assets.static_assets.base import StaticAssetFactory
from infinigen.core.tagging import tag_support_surfaces
from infinigen.core.util import blender as butil
from infinigen.core.util.math import FixedSeed

STATIC_ASSET_BBOX_CACHE = {}
REPO_ROOT = Path(__file__).resolve().parents[3]


def static_category_factory(
    path_to_assets: str,
    tag_support=False,
    x_dim: float = None,
    y_dim: float = None,
    z_dim: float = None,
    rotation_euler: tuple[float] = None,
    extensions: tuple[str, ...] | None = None,
    filenames: tuple[str, ...] | None = None,
) -> StaticAssetFactory:
    """
    Create a factory for external asset import.
    tag_support: tag the planes of the object that are parallel to xy plane as support surfaces (e.g. shelves)
    x_dim, y_dim, z_dim: specify ONLY ONE dimension for the imported object. The object will be scaled accordingly.
    rotation_euler: sets the rotation of the object in euler angles. The object will not be rotated if not specified.
    """

    class StaticCategoryFactory(StaticAssetFactory):
        def __init__(self, factory_seed, coarse=False):
            super().__init__(factory_seed, coarse)
            with FixedSeed(factory_seed):
                resolved_asset_dir = Path(path_to_assets)
                if not resolved_asset_dir.is_absolute():
                    resolved_asset_dir = REPO_ROOT / resolved_asset_dir
                self.path_to_assets = str(resolved_asset_dir)
                self.tag_support = tag_support
                self.asset_dir = self.path_to_assets
                self.x_dim, self.y_dim, self.z_dim = x_dim, y_dim, z_dim
                self.rotation_euler = rotation_euler
                self.extensions = (
                    tuple(ext.lower().lstrip(".") for ext in extensions)
                    if extensions is not None
                    else tuple(self.import_map.keys())
                )
                self.filenames = set(filenames) if filenames is not None else None
                asset_files = [
                    f
                    for f in os.listdir(self.asset_dir)
                    if f.rsplit(".", 1)[-1].lower() in self.extensions
                    and (self.filenames is None or f in self.filenames)
                ]
                if not asset_files or len(asset_files) == 0:
                    raise ValueError(
                        f"No valid asset files found in {self.asset_dir} "
                        f"for extensions {self.extensions} "
                        f"and filenames {sorted(self.filenames) if self.filenames is not None else 'ANY'}"
                    )
                self.asset_file = random.choice(asset_files)

        def _apply_scale(self, imported_obj: bpy.types.Object):
            if (
                self.x_dim is None
                and self.y_dim is None
                and self.z_dim is None
            ):
                return

            if (
                sum(
                    [
                        1
                        for dim in [self.x_dim, self.y_dim, self.z_dim]
                        if dim is not None
                    ]
                )
                != 1
            ):
                raise ValueError("Only one dimension can be provided")

            if self.x_dim is not None:
                denom = imported_obj.dimensions[0]
                target = self.x_dim
            elif self.y_dim is not None:
                denom = imported_obj.dimensions[1]
                target = self.y_dim
            else:
                denom = imported_obj.dimensions[2]
                target = self.z_dim
            if abs(denom) < 1e-6:
                raise ValueError(
                    f"Imported asset {self.asset_file} has near-zero dimension {denom}"
                )
            scale = target / denom
            imported_obj.scale = (scale, scale, scale)
            butil.apply_transform(imported_obj, loc=False, rot=False, scale=True)

        def _apply_rotation(self, imported_obj: bpy.types.Object):
            if self.rotation_euler is None:
                return
            imported_obj.rotation_euler = self.rotation_euler
            butil.apply_transform(imported_obj, loc=False, rot=True, scale=False)

        def _bbox_cache_key(self):
            return (
                os.path.join(self.asset_dir, self.asset_file),
                self.x_dim,
                self.y_dim,
                self.z_dim,
                self.rotation_euler,
            )

        def _placeholder_bounds(self):
            key = self._bbox_cache_key()
            if key not in STATIC_ASSET_BBOX_CACHE:
                imported_obj = self.import_file(key[0])
                self._apply_scale(imported_obj)
                self._apply_rotation(imported_obj)
                bounds = np.array(imported_obj.bound_box, dtype=float)
                STATIC_ASSET_BBOX_CACHE[key] = (
                    bounds.min(axis=0),
                    bounds.max(axis=0),
                )
                butil.delete(list(butil.iter_object_tree(imported_obj)))
            return STATIC_ASSET_BBOX_CACHE[key]

        def create_placeholder(self, **kwargs) -> bpy.types.Object:
            min_corner, max_corner = self._placeholder_bounds()
            return box_from_corners(min_corner, max_corner)

        def create_asset(self, **params) -> bpy.types.Object:
            file_path = os.path.join(self.asset_dir, self.asset_file)
            imported_obj = self.import_file(file_path)
            self._apply_scale(imported_obj)
            self._apply_rotation(imported_obj)
            if self.tag_support:
                tag_support_surfaces(imported_obj)

            if imported_obj:
                return imported_obj
            else:
                raise ValueError(f"Failed to import asset: {self.asset_file}")

    return StaticCategoryFactory


# Source-only dental / hospital assets
StaticBenchFactory = static_category_factory(
    "infinigen/assets/static_assets/source/Bench",
    extensions=("fbx",),
)
StaticCabinetFactory = static_category_factory(
    "infinigen/assets/static_assets/source/Cabinet",
    extensions=("fbx",),
)
StaticShelfFactory = static_category_factory(
    "infinigen/assets/static_assets/source/Shelf",
    tag_support=True,
    z_dim=2,
    extensions=("fbx",),
)
StaticChairFactory = static_category_factory(
    "infinigen/assets/static_assets/source/Chair",
    extensions=("fbx",),
)
StaticDentalunitFactory = static_category_factory(
    "infinigen/assets/static_assets/source/Dentalunit",
    extensions=("fbx",),
)
StaticFronttableFactory = static_category_factory(
    "infinigen/assets/static_assets/source/Fronttable",
    extensions=("fbx",),
)
StaticInternchairFactory = static_category_factory(
    "infinigen/assets/static_assets/source/Internchair",
    extensions=("fbx",),
)
StaticRectangleFactory = static_category_factory(
    "infinigen/assets/static_assets/source/Rectangle",
    extensions=("fbx",),
)
StaticSofaFactory = static_category_factory(
    "infinigen/assets/static_assets/source/Sofa",
    extensions=("fbx",),
)
StaticTableFactory = static_category_factory(
    "infinigen/assets/static_assets/source/Table",
    extensions=("fbx",),
)
