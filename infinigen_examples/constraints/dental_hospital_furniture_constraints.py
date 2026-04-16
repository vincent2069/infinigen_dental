# Copyright (C) 2023, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory
# of this source tree.

# Authors: Dental hospital furniture constraints for source-only clinic scenes

from collections import OrderedDict

import infinigen.assets.static_assets as static_assets
from infinigen.core.constraints import constraint_language as cl
from infinigen.core.constraints import usage_lookup
from infinigen.core.tags import Semantics

from . import util as cu
from .dental_hospital_semantics import (
    StaticWashbarFactory,
    dental_hospital_asset_usage,
)


def dental_hospital_furniture_constraints():
    """Construct source-only furniture constraints for a dental hospital.

    Design goals for this preset:
    - only use assets from ``static_assets/source``
    - make waiting / reception look orderly instead of cluttered
    - ensure every clinic clearly contains a dental unit
    - avoid fragile child-object / ceiling-light stages
    """

    used_as = dental_hospital_asset_usage()
    usage_lookup.initialize_from_dict(used_as)

    constraints = OrderedDict()
    score_terms = OrderedDict()

    rooms = cl.scene()[{Semantics.Room, -Semantics.Object}]
    obj = cl.scene()[{Semantics.Object, -Semantics.Room}]
    cutters = cl.scene()[Semantics.Cutter]
    doors = cutters[Semantics.Door]

    waiting_room = rooms[Semantics.HospitalWaitingRoom]
    reception_room = rooms[Semantics.HospitalReception]
    clinic_room = rooms[Semantics.HospitalClinic]
    vip_clinic = rooms[Semantics.HospitalVIPClinic]
    corridor = rooms[Semantics.HospitalCorridor]
    sterilization_room = rooms[Semantics.HospitalTreatmentRoom]
    consultation_room = rooms[Semantics.HospitalExaminationRoom]

    furniture = obj[Semantics.Furniture].related_to(rooms, cu.on_floor)

    dental_unit = obj[static_assets.StaticDentalunitFactory].related_to(
        rooms, cu.on_floor
    )
    sink = obj[Semantics.Sink].related_to(rooms, cu.on_floor).related_to(
        rooms, cu.against_wall
    )
    washbar = obj[StaticWashbarFactory].related_to(rooms, cu.on_floor).related_to(
        rooms, cu.against_wall
    )
    staff_chair = obj[static_assets.StaticInternchairFactory].related_to(
        rooms, cu.on_floor
    )
    cabinet = (
        obj[static_assets.StaticCabinetFactory]
        .related_to(rooms, cu.on_floor)
        .related_to(rooms, cu.against_wall)
    )
    table = obj[static_assets.StaticTableFactory].related_to(rooms, cu.on_floor)
    wall_table = table.related_to(rooms, cu.against_wall)
    bench = obj[static_assets.StaticBenchFactory].related_to(rooms, cu.on_floor)
    chair = obj[static_assets.StaticChairFactory].related_to(rooms, cu.on_floor)
    sofa = (
        obj[static_assets.StaticSofaFactory]
        .related_to(rooms, cu.on_floor)
        .related_to(rooms, cu.against_wall)
    )
    lounge_table = obj[static_assets.StaticRectangleFactory].related_to(
        rooms, cu.on_floor
    )
    front_desk = (
        obj[static_assets.StaticFronttableFactory]
        .related_to(rooms, cu.on_floor)
        .related_to(rooms, cu.against_wall)
    )

    # region Waiting + reception

    constraints["waiting_room"] = waiting_room.all(
        lambda r: (
            bench.related_to(r).count().in_range(4, 8)
            * lounge_table.related_to(r).count().in_range(0, 1)
            * chair.related_to(r).count().in_range(0, 2)
        )
    )
    score_terms["waiting_room"] = waiting_room.mean(
        lambda r: (
            bench.related_to(r).mean(
                lambda b: (
                    b.distance(r, cu.walltags).hinge(0.8, 2.6).maximize(weight=7)
                    + b.distance(bench.related_to(r))
                    .hinge(0.7, 1.5)
                    .maximize(weight=5)
                    + cl.angle_alignment_cost(b, r, cu.walltags).minimize(weight=3)
                    + cl.accessibility_cost(b, r, dist=0.9).minimize(weight=2)
                )
            )
            + lounge_table.related_to(r).mean(
                lambda t: (
                    cl.center_stable_surface_dist(t).minimize(weight=3)
                    + cl.angle_alignment_cost(t, r, cu.walltags).minimize(weight=1)
                    + t.distance(bench.related_to(r))
                    .hinge(0.8, 2.2)
                    .maximize(weight=2)
                )
            )
            + chair.related_to(r).mean(
                lambda c: (
                    c.distance(lounge_table.related_to(r))
                    .hinge(0.5, 1.4)
                    .maximize(weight=2)
                    + c.distance(bench.related_to(r))
                    .hinge(0.8, 2.0)
                    .maximize(weight=1)
                    + c.distance(r, cu.walltags).hinge(0.3, 1.4).maximize(weight=1)
                )
            )
        )
    )

    constraints["reception"] = reception_room.all(
        lambda r: (
            front_desk.related_to(r).count().equals(1)
            * staff_chair.related_to(r).count().in_range(1, 2)
            * cabinet.related_to(r).count().in_range(0, 1)
            * chair.related_to(r).count().equals(0)
        )
    )
    score_terms["reception"] = reception_room.mean(
        lambda r: (
            front_desk.related_to(r).mean(
                lambda d: (
                    cl.angle_alignment_cost(d, r, cu.walltags).minimize(weight=6)
                    + cl.accessibility_cost(d, r, dist=1.3).minimize(weight=6)
                    + d.distance(doors.related_to(r)).hinge(0.8, 2.4).maximize(weight=4)
                )
            )
            + staff_chair.related_to(r).mean(
                lambda c: (
                    c.distance(front_desk.related_to(r))
                    .hinge(0.35, 0.85)
                    .maximize(weight=5)
                    + c.distance(staff_chair.related_to(r))
                    .hinge(0.35, 0.8)
                    .maximize(weight=1)
                )
            )
            + cabinet.related_to(r).mean(
                lambda c: c.distance(front_desk.related_to(r))
                .hinge(0.5, 1.6)
                .maximize(weight=1)
            )
        )
    )

    # endregion

    # region Standard clinics

    constraints["clinic"] = clinic_room.all(
        lambda r: (
            dental_unit.related_to(r).count().equals(1)
            * washbar.related_to(r).count().equals(1)
            * staff_chair.related_to(r).count().in_range(1, 2)
            * cabinet.related_to(r).count().in_range(1, 2)
            * wall_table.related_to(r).count().in_range(0, 1)
        )
    )
    score_terms["clinic"] = clinic_room.mean(
        lambda r: (
            cl.center_stable_surface_dist(dental_unit.related_to(r)).minimize(weight=8)
            + dental_unit.related_to(r)
            .distance(r, cu.walltags)
            .hinge(0.8, 2.4)
            .maximize(weight=4)
            + cl.angle_alignment_cost(dental_unit.related_to(r), r, cu.walltags).minimize(
                weight=3
            )
            + cl.accessibility_cost(dental_unit.related_to(r), r, dist=1.1).minimize(
                weight=7
            )
            + staff_chair.related_to(r).mean(
                lambda s: s.distance(dental_unit.related_to(r))
                .hinge(0.6, 1.6)
                .maximize(weight=3)
            )
            + washbar.related_to(r).mean(
                lambda s: (
                    cl.angle_alignment_cost(s, r, cu.walltags).minimize(weight=2)
                    + s.distance(doors.related_to(r)).hinge(0.6, 2.0).maximize(weight=1)
                    + s.distance(dental_unit.related_to(r))
                    .hinge(1.4, 3.2)
                    .maximize(weight=3)
                )
            )
            + cabinet.related_to(r).mean(
                lambda c: (
                    c.distance(r, cu.walltags).maximize(weight=1)
                    + c.distance(dental_unit.related_to(r))
                    .hinge(1.4, 3.2)
                    .maximize(weight=3)
                )
            )
            + wall_table.related_to(r).mean(
                lambda t: (
                    cl.angle_alignment_cost(t, r, cu.walltags).minimize(weight=1)
                    + t.distance(dental_unit.related_to(r))
                    .hinge(1.3, 3.0)
                    .maximize(weight=3)
                )
            )
        )
    )

    # endregion

    # region VIP clinics with lounge area

    constraints["vip_clinic"] = vip_clinic.all(
        lambda r: (
            dental_unit.related_to(r).count().equals(1)
            * washbar.related_to(r).count().equals(1)
            * staff_chair.related_to(r).count().in_range(1, 2)
            * cabinet.related_to(r).count().in_range(1, 3)
            * wall_table.related_to(r).count().in_range(0, 1)
            * sofa.related_to(r).count().equals(1)
            * lounge_table.related_to(r).count().equals(1)
            * chair.related_to(r).count().in_range(0, 2)
        )
    )
    score_terms["vip_clinic"] = vip_clinic.mean(
        lambda r: (
            cl.center_stable_surface_dist(dental_unit.related_to(r)).minimize(weight=7)
            + dental_unit.related_to(r)
            .distance(r, cu.walltags)
            .hinge(0.8, 2.5)
            .maximize(weight=3)
            + cl.angle_alignment_cost(dental_unit.related_to(r), r, cu.walltags).minimize(
                weight=3
            )
            + cl.accessibility_cost(dental_unit.related_to(r), r, dist=1.1).minimize(
                weight=7
            )
            + washbar.related_to(r).mean(
                lambda s: (
                    cl.angle_alignment_cost(s, r, cu.walltags).minimize(weight=2)
                    + s.distance(dental_unit.related_to(r))
                    .hinge(1.5, 3.4)
                    .maximize(weight=3)
                )
            )
            + sofa.related_to(r).mean(
                lambda s: (
                    cl.angle_alignment_cost(s, r, cu.walltags).minimize(weight=1)
                    + s.distance(dental_unit.related_to(r))
                    .hinge(2.6, 5.4)
                    .maximize(weight=5)
                )
            )
            + lounge_table.related_to(r).mean(
                lambda t: (
                    cl.angle_alignment_cost(t, r, cu.walltags).minimize(weight=1)
                    + t.distance(sofa.related_to(r)).hinge(0.6, 1.6).maximize(weight=3)
                    + t.distance(dental_unit.related_to(r))
                    .hinge(2.4, 5.0)
                    .maximize(weight=4)
                )
            )
            + chair.related_to(r).mean(
                lambda c: (
                    c.distance(lounge_table.related_to(r))
                    .hinge(0.6, 1.4)
                    .maximize(weight=2)
                    + c.distance(dental_unit.related_to(r))
                    .hinge(2.2, 4.8)
                    .maximize(weight=2)
                )
            )
            + cabinet.related_to(r).mean(
                lambda c: (
                    c.distance(dental_unit.related_to(r))
                    .hinge(1.4, 3.6)
                    .maximize(weight=3)
                    + c.distance(sofa.related_to(r)).hinge(0.6, 2.0).maximize(weight=1)
                )
            )
            + wall_table.related_to(r).mean(
                lambda t: (
                    cl.angle_alignment_cost(t, r, cu.walltags).minimize(weight=1)
                    + t.distance(dental_unit.related_to(r))
                    .hinge(1.4, 3.2)
                    .maximize(weight=3)
                )
            )
        )
    )

    # endregion

    # region Dental support core

    constraints["consultation_room"] = consultation_room.all(
        lambda r: (
            sink.related_to(r).count().in_range(0, 1)
            * cabinet.related_to(r).count().in_range(1, 2)
            * chair.related_to(r).count().in_range(2, 4)
            * lounge_table.related_to(r).count().equals(1)
        )
    )
    constraints["sterilization_room"] = sterilization_room.all(
        lambda r: (
            sink.related_to(r).count().equals(1)
            * cabinet.related_to(r).count().in_range(2, 3)
            * staff_chair.related_to(r).count().in_range(0, 1)
            * wall_table.related_to(r).count().in_range(1, 2)
        )
    )

    score_terms["support_rooms"] = consultation_room.mean(
        lambda r: (
            chair.related_to(r).mean(
                lambda c: c.distance(lounge_table.related_to(r))
                .hinge(0.6, 1.5)
                .maximize(weight=2)
            )
            + cabinet.related_to(r).mean(
                lambda c: c.distance(doors.related_to(r)).maximize(weight=1)
            )
        )
    ) + sterilization_room.mean(
        lambda r: (
            sink.related_to(r).mean(
                lambda s: s.distance(cabinet.related_to(r))
                .hinge(0.4, 1.6)
                .maximize(weight=2)
            )
            + cabinet.related_to(r).mean(
                lambda c: c.distance(wall_table.related_to(r))
                .hinge(0.3, 1.4)
                .maximize(weight=1)
            )
        )
    )

    # endregion

    constraints["corridor"] = corridor.all(
        lambda r: furniture.related_to(r).count().equals(0)
    )

    return cl.Problem(constraints=constraints, score_terms=score_terms)
