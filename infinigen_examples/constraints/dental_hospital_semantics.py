# Copyright (C) 2023, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory
# of this source tree.

# Authors: Dental hospital semantics restricted to source-folder assets only

import infinigen.assets.static_assets as static_assets
from infinigen.core.tags import Semantics


StaticWashbarFactory = static_assets.static_category_factory(
    "infinigen/assets/static_assets/source/Washbar",
    extensions=("fbx",),
    filenames=("washbar1.fbx",),
)
StaticDeskTableFactory = static_assets.static_category_factory(
    "infinigen/assets/static_assets/source/Table",
    extensions=("fbx",),
    filenames=("table4.fbx",),
)
StaticLoungeTableFactory = static_assets.static_category_factory(
    "infinigen/assets/static_assets/source/Rectangle",
    extensions=("fbx",),
    filenames=("rectangletable1.fbx",),
)
StaticVipSofaFactory = static_assets.static_category_factory(
    "infinigen/assets/static_assets/source/Sofa",
    extensions=("fbx",),
    filenames=("sofa2.fbx",),
)


def dental_hospital_asset_usage():
    """Use only assets shipped under ``static_assets/source``.

    The user explicitly requested that the dental preset should avoid all
    external / procedural furniture generators. We therefore keep the semantic
    map intentionally small and source-only:
    - waiting / reception / clinic furniture all come from ``source/*``
    - no decorative small props
    - no child-object placement on cabinets / tables
    - no ceiling-light generators, so the on_ceiling stage becomes empty
    """

    seating_factories = {
        static_assets.StaticBenchFactory,
        static_assets.StaticChairFactory,
        StaticVipSofaFactory,
        static_assets.StaticInternchairFactory,
    }
    table_factories = {
        StaticDeskTableFactory,
        StaticLoungeTableFactory,
        static_assets.StaticFronttableFactory,
    }
    storage_factories = {
        static_assets.StaticCabinetFactory,
    }
    sink_factories = {
        StaticWashbarFactory,
    }

    all_furniture_factories = set().union(
        seating_factories,
        table_factories,
        storage_factories,
        sink_factories,
        {
            static_assets.StaticDentalunitFactory,
        },
    )

    used_as = {
        Semantics.Seating: seating_factories,
        Semantics.LoungeSeating: {
            StaticVipSofaFactory,
            static_assets.StaticChairFactory,
        },
        Semantics.Table: table_factories,
        Semantics.Storage: storage_factories,
        Semantics.Sink: sink_factories,
        Semantics.Furniture: all_furniture_factories,
        Semantics.Object: all_furniture_factories,
        Semantics.RealPlaceholder: all_furniture_factories,
        Semantics.AssetAsPlaceholder: set(),
        Semantics.AssetPlaceholderForChildren: set(),
        Semantics.PlaceholderBBox: set(),
        Semantics.SingleGenerator: set(),
        Semantics.NoRotation: set(),
        Semantics.NoCollision: set(),
        Semantics.NoChildren: set(all_furniture_factories),
        # Keep lookup keys present even though this source-only preset does not
        # use decorative child objects.
        Semantics.OfficeShelfItem: set(),
        Semantics.TableDisplayItem: set(),
        Semantics.KitchenCounterItem: set(),
    }

    return used_as
