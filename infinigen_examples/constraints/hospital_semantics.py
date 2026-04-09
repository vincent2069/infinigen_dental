# Copyright (C) 2023, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory
# of this source tree.

# Authors: Hospital scene semantics for generating large hospital environments

import infinigen.assets.static_assets as static_assets
from infinigen.assets.objects import (
    appliances,
    bathroom,
    decor,
    elements,
    lamp,
    seating,
    shelves,
    table_decorations,
    tables,
    tableware,
    wall_decorations,
)
from infinigen.core.tags import Semantics


def hospital_asset_usage():
    """Defines what generators are considered to fulfill what roles in a hospital setting.

    This maps asset factories to semantic roles specific to hospital environments.
    Uses existing Semantics tags for compatibility with the constraint system.

    IMPORTANT: Factories that should be findable by multiple tags (e.g., Furniture AND Seating)
    must be explicitly added to each category.

    """

    used_as = {}

    # region Hospital-specific furniture using existing semantics

    # Seating - 座椅 (also added to Furniture below)
    seating_factories = {
        static_assets.StaticBenchFactory,
        static_assets.StaticChairFactory,
        static_assets.StaticSofaFactory,
        seating.SofaFactory,
        seating.ChairFactory,
        seating.ArmChairFactory,
        seating.OfficeChairFactory,
    }
    used_as[Semantics.Seating] = seating_factories

    # LoungeSeating - 休闲座椅
    used_as[Semantics.LoungeSeating] = {
        static_assets.StaticSofaFactory,
        seating.SofaFactory,
        seating.ArmChairFactory,
    }

    # Tables (also added to Furniture below) - 桌子
    table_factories = {
        static_assets.StaticTableFactory,
        static_assets.StaticFronttableFactory,
        tables.TableCocktailFactory,
        tables.TableDiningFactory,
        shelves.SimpleDeskFactory,
    }
    used_as[Semantics.Table] = table_factories

    used_as[Semantics.SideTable] = {
        shelves.SidetableDeskFactory,
        tables.SideTableFactory,
    }

    # Storage (also added to Furniture below) - 储物柜
    storage_factories = {
        static_assets.StaticCabinetFactory,
        # NOTE: StaticShelfFactory points to
        # infinigen/assets/static_assets/source/Shelf, but this dental-hospital
        # asset pack does not ship that directory. Keep to valid cabinet/storage
        # generators so the solver never samples a missing static shelf asset.
        shelves.SimpleBookcaseFactory,
        shelves.CellShelfFactory,
        shelves.LargeShelfFactory,
        shelves.SingleCabinetFactory,
        shelves.KitchenCabinetFactory,
    }
    used_as[Semantics.Storage] = storage_factories

    # Furniture - main category that includes seating, tables, storage, etc.
    # This MUST include all factories that are in Seating, Table, or Storage
    all_furniture_factories = set().union(
        seating_factories,
        table_factories,
        storage_factories,
        {
            static_assets.StaticDentalunitFactory,
            static_assets.StaticInternchairFactory,
            bathroom.BathtubFactory,
        },
    )
    used_as[Semantics.Furniture] = all_furniture_factories

    # Object - base category for all physical objects
    # This is required by the constraint system's lookup_generator
    used_as[Semantics.Object] = all_furniture_factories.union(
        used_as.get(Semantics.OfficeShelfItem, set()),
        used_as.get(Semantics.TableDisplayItem, set()),
        used_as.get(Semantics.KitchenCounterItem, set()),
        {
            wall_decorations.MirrorFactory,
            wall_decorations.WallArtFactory,
            lamp.CeilingLightFactory,
        },
    )

    # endregion

    # region Small objects for hospital

    # Office supplies for desk - 办公桌用品
    used_as[Semantics.OfficeShelfItem] = {
        table_decorations.BookStackFactory,
        table_decorations.BookColumnFactory,
        elements.NatureShelfTrinketsFactory,
    }

    # Plants for decoration - 装饰植物
    used_as[Semantics.TableDisplayItem] = {
        tableware.PlantContainerFactory,
        tableware.LargePlantContainerFactory,
        table_decorations.VaseFactory,
    }

    # Desk items
    used_as[Semantics.KitchenCounterItem] = {
        table_decorations.BookColumnFactory,
        tableware.JarFactory,
    }

    # endregion

    # region Asset metadata

    used_as[Semantics.RealPlaceholder] = set().union(
        seating_factories,
        table_factories,
        storage_factories,
        {
            # These static hospital assets are used heavily during solving. Keep
            # them as simple placeholders until the final populate step so the
            # solver does not repeatedly import FBX meshes/materials and crash
            # Blender with runaway memory growth.
            static_assets.StaticDentalunitFactory,
            static_assets.StaticInternchairFactory,
        },
    )

    # The example solver unconditionally queries these metadata tags via
    # usage_lookup.has_usage(...), so they must always exist in the lookup even
    # when this scene does not actively use them.
    used_as[Semantics.AssetAsPlaceholder] = set()

    used_as[Semantics.AssetPlaceholderForChildren] = set().union(
        storage_factories,
    )

    used_as[Semantics.PlaceholderBBox] = set()
    used_as[Semantics.SingleGenerator] = set()

    used_as[Semantics.NoRotation] = set().union(
        seating_factories,
        storage_factories,
    )

    used_as[Semantics.NoCollision] = set()

    used_as[Semantics.NoChildren] = {
        wall_decorations.MirrorFactory,
        wall_decorations.WallArtFactory,
        lamp.CeilingLightFactory,
    }

    # endregion

    return used_as
