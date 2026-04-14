# Copyright (C) 2023, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory
# of this source tree.

# Authors: Dental hospital semantics extending the hospital scene support

import infinigen.assets.static_assets as static_assets
from infinigen.assets.objects import bathroom
from infinigen.core.tags import Semantics

from .hospital_semantics import hospital_asset_usage


StaticWashbarFactory = static_assets.static_category_factory(
    "infinigen/assets/static_assets/source/Washbar"
)


def dental_hospital_asset_usage():
    """Extend the hospital asset map with dental-clinic specific utilities.

    The hospital setup already contains the key dental chair, reception, seating,
    table, and cabinet assets. For dental clinics we additionally require
    reusable sink / washbar assets so every clinic can be constrained to contain
    one wall-side hand-washing station.
    """

    used_as = {k: set(v) for k, v in hospital_asset_usage().items()}

    sink_factories = {
        bathroom.StandingSinkFactory,
        StaticWashbarFactory,
    }
    lounge_table_factories = {
        static_assets.StaticRectangleFactory,
    }

    used_as[Semantics.Sink] = sink_factories
    used_as[Semantics.Table] = used_as.get(Semantics.Table, set()).union(
        lounge_table_factories
    )
    used_as[Semantics.Furniture] = used_as.get(Semantics.Furniture, set()).union(
        sink_factories, lounge_table_factories
    )
    used_as[Semantics.Object] = used_as.get(Semantics.Object, set()).union(
        sink_factories, lounge_table_factories
    )
    used_as[Semantics.RealPlaceholder] = used_as.get(
        Semantics.RealPlaceholder, set()
    ).union(sink_factories, lounge_table_factories)
    used_as[Semantics.NoRotation] = used_as.get(Semantics.NoRotation, set()).union(
        sink_factories, lounge_table_factories
    )
    used_as[Semantics.NoChildren] = used_as.get(Semantics.NoChildren, set()).union(
        sink_factories
    )

    return used_as
