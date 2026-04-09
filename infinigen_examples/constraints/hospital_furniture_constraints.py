# Copyright (C) 2023, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory
# of this source tree.

# Authors: Hospital furniture constraints for generating large hospital environments

import numpy as np

from infinigen.assets.objects import lamp, tableware, wall_decorations
from infinigen.core.constraints import constraint_language as cl
from infinigen.core.constraints import usage_lookup
from infinigen.core.tags import Semantics

from . import util as cu
from .hospital_semantics import hospital_asset_usage


def sample_hospital_constraint_params():
    """Sample constraint parameters specific to hospital environments."""
    return dict(
        # What pct of the room floorplan should we try to fill with furniture?
        furniture_fullness_pct=0.4,  # Hospitals are less cluttered than homes
        # How many objects on storage furniture per unit of volume
        obj_interior_obj_pct=0.3,  # Medical cabinets are organized, not cluttered
        # What pct of top surface of storage furniture should be filled
        obj_on_storage_pct=0.2,  # Clean surfaces for hygiene
        # What pct of top surface of NON-STORAGE objects should be filled
        obj_on_nonstorage_pct=0.15,  # Minimal items on desks for cleanliness
    )


def hospital_furniture_constraints():
    """Construct a constraint graph for hospital furniture placement.

    Hospital furniture layout rules:
    - Waiting Room: Benches/chairs arranged for patient comfort
    - Reception: Desk with chair, positioned near entrance
    - Clinics: Doctor desk, patient chair, examination table, cabinets
    - Corridors: Clear path, minimal obstacles

    """

    used_as = hospital_asset_usage()
    usage_lookup.initialize_from_dict(used_as)

    rooms = cl.scene()[{Semantics.Room, -Semantics.Object}]
    obj = cl.scene()[{Semantics.Object, -Semantics.Room}]

    cutters = cl.scene()[Semantics.Cutter]
    window = cutters[Semantics.Window]
    doors = cutters[Semantics.Door]

    constraints = {}
    score_terms = {}

    params = sample_hospital_constraint_params()

    # Get hospital-specific furniture categories using standard semantics
    furniture = obj[Semantics.Furniture].related_to(rooms, cu.on_floor)
    seating = furniture[Semantics.Seating]
    storage = furniture[Semantics.Storage]
    tables_furn = furniture[Semantics.Table]

    # region WAITING ROOM FURNITURE

    waiting_room = rooms[Semantics.HospitalWaitingRoom]

    # Waiting benches/chairs should be arranged along walls
    constraints["waiting_room"] = waiting_room.all(
        lambda r: (
            # Have enough seating for a waiting room
            seating.related_to(r).count().in_range(6, 20)
        )
    )

    score_terms["waiting_room"] = waiting_room.mean(
        lambda r: (
            # Seating should be against walls or arranged in rows
            seating.related_to(r)
            .mean(lambda s: (
                s.distance(r, cu.walltags).maximize(weight=2)
                + s.distance(seating).hinge(0.5, 1.5).maximize(weight=1)
            ))
            # Add coffee table in center
            + tables_furn.related_to(r)
            .mean(lambda t: cl.center_stable_surface_dist(t).minimize(weight=2))
        )
    )

    # endregion

    # region RECEPTION AREA

    reception_room = rooms[Semantics.HospitalReception]

    constraints["reception"] = reception_room.all(
        lambda r: (
            # Reception desk (table) near entrance
            tables_furn.related_to(r).count().in_range(1, 3)
        )
    )

    score_terms["reception"] = reception_room.mean(
        lambda r: (
            tables_furn.related_to(r).mean(
                lambda t: (
                    # Desk should be accessible from entrance
                    t.distance(doors).minimize(weight=5)
                    # Office chair behind the desk
                    + obj[Semantics.Furniture]
                    .related_to(t, cu.front_to_front)
                    .count()
                    .hinge(0, 2)
                    .minimize(weight=2)
                )
            )
        )
    )

    # endregion

    # region CLINIC / EXAMINATION ROOMS

    clinic_room = rooms[Semantics.HospitalClinic]
    vip_clinic = rooms[Semantics.HospitalVIPClinic]

    constraints["clinic"] = clinic_room.all(
        lambda r: (
            # Each clinic needs desk and chairs
            tables_furn.related_to(r).count().in_range(1, 3)
            # At least some seating
            * seating.related_to(r).count().in_range(2, 6)
            # Storage cabinet
            * storage.related_to(r).count().in_range(0, 3)
        )
    )

    # VIP clinics get additional furniture
    constraints["vip_clinic"] = vip_clinic.all(
        lambda r: (
            storage.related_to(r).count().in_range(1, 4)
            * seating.related_to(r).count().in_range(3, 8)
        )
    )

    score_terms["clinic"] = clinic_room.mean(
        lambda r: (
            # Desk against wall, away from door
            tables_furn.related_to(r).mean(
                lambda t: (
                    t.distance(r, cu.walltags).maximize(weight=3)
                    + t.distance(doors).minimize(weight=2)
                    + cl.accessibility_cost(t, r).minimize(weight=3)
                )
            )
            # Seating near desk
            + seating.related_to(r).mean(
                lambda s: (
                    s.distance(tables_furn.related_to(r))
                    .hinge(0.5, 2.0)
                    .maximize(weight=2)
                )
            )
        )
    )

    score_terms["vip_clinic"] = vip_clinic.mean(
        lambda r: (
            # Storage against walls
            storage.related_to(r).mean(
                lambda s: s.distance(r, cu.walltags).maximize(weight=3)
            )
        )
    )

    # endregion

    # region CORRIDOR

    corridor = rooms[Semantics.HospitalCorridor]

    # Corridors should be mostly clear for traffic
    constraints["corridor"] = corridor.all(
        lambda r: (
            # Minimal furniture in corridors
            obj[Semantics.Furniture].related_to(r, cu.on_floor).count().in_range(0, 2)
        )
    )

    score_terms["corridor"] = corridor.mean(
        lambda r: (
            # Keep walkway clear (center of corridor)
            cl.center_stable_surface_dist(obj.related_to(r, cu.on_floor)).maximize(
                weight=5
            )
        )
    )

    # endregion

    # region STORAGE

    constraints["storage"] = (
        clinic_room.all(
            lambda r: (
                storage.related_to(r).all(
                    lambda s: (
                        # Cabinets against walls
                        s.distance(r, cu.walltags).in_range(0, 0.1)
                    )
                )
            )
        )
        * vip_clinic.all(
            lambda r: (
                storage.related_to(r).all(
                    lambda s: (
                        # Cabinets against walls
                        s.distance(r, cu.walltags).in_range(0, 0.1)
                    )
                )
            )
        )
    )

    score_terms["storage"] = (
        clinic_room.mean(
            lambda r: (
                storage.related_to(r)
                .mean(
                    lambda s: (
                        cl.accessibility_cost(s, r).minimize(weight=3)
                        + s.distance(tables_furn.related_to(r)).hinge(0.5, 3).maximize(
                            weight=1
                        )
                    )
                )
            )
        )
        + vip_clinic.mean(
            lambda r: (
                storage.related_to(r)
                .mean(
                    lambda s: (
                        cl.accessibility_cost(s, r).minimize(weight=3)
                        + s.distance(tables_furn.related_to(r)).hinge(0.5, 3).maximize(
                            weight=1
                        )
                    )
                )
            )
        )
    )

    # endregion

    # region PLANTS FOR DECORATION
    # NOTE: Plants are temporarily disabled because PlantContainerFactory
    # is covered by multiple greedy stages (on_floor_and_wall, on_wall, etc.)
    # which violates the non-overlapping stage requirement.
    # Can be re-enabled by restricting plants to a single stage.

    # plants = obj[tableware.PlantContainerFactory]
    # constraints["plants"] = (...)
    # score_terms["plants"] = (...)

    # endregion

    # region LIGHTING
    # NOTE: Lighting is temporarily disabled because Semantics.Lighting
    # is covered by multiple greedy stages which violates the non-overlapping
    # stage requirement.
    # Lighting will be handled by the default indoor lighting system.

    # lights = obj[Semantics.Lighting]
    # constraints["lighting"] = rooms.all(...)

    # endregion

    # region WALL DECORATIONS
    # NOTE: Wall decorations are temporarily disabled because
    # Semantics.WallDecoration factories are not registered in hospital_semantics.
    # Can be re-enabled by adding wall_decorations factories to the semantic mapping.

    # walldec = obj[Semantics.WallDecoration].related_to(rooms, cu.flush_wall)
    # constraints["wall_decorations"] = ...
    # score_terms["wall_decorations"] = ...

    # endregion

    return cl.Problem(constraints=constraints, score_terms=score_terms)
