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
    StaticDeskTableFactory,
    StaticLoungeTableFactory,
    StaticVipSofaFactory,
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
    windows = cutters[Semantics.Window]
    openings = cutters[Semantics.Open]

    waiting_room = rooms[Semantics.HospitalWaitingRoom]
    reception_room = rooms[Semantics.HospitalReception]
    clinic_room = rooms[Semantics.HospitalClinic]
    vip_clinic = rooms[Semantics.HospitalVIPClinic]
    corridor = rooms[Semantics.HospitalCorridor]
    sterilization_room = rooms[Semantics.HospitalTreatmentRoom]
    consultation_room = rooms[Semantics.HospitalExaminationRoom]

    casework_against_wall = cl.StableAgainst(cu.back, cu.walltags, margin=0.12)
    frontdesk_against_wall = cl.StableAgainst(cu.back, cu.walltags, margin=0.45)

    furniture = obj[Semantics.Furniture].related_to(rooms, cu.on_floor)

    dental_unit = obj[static_assets.StaticDentalunitFactory].related_to(rooms, cu.on_floor)
    sink = obj[Semantics.Sink].related_to(rooms, cu.on_floor).related_to(
        rooms, casework_against_wall
    )
    washbar = obj[StaticWashbarFactory].related_to(rooms, cu.on_floor).related_to(
        rooms, casework_against_wall
    )
    staff_chair = obj[static_assets.StaticInternchairFactory].related_to(
        rooms, cu.on_floor
    )
    cabinet = (
        obj[static_assets.StaticCabinetFactory]
        .related_to(rooms, cu.on_floor)
        .related_to(rooms, casework_against_wall)
    )
    desk_table = obj[StaticDeskTableFactory].related_to(rooms, cu.on_floor)
    wall_table = desk_table.related_to(rooms, casework_against_wall)
    bench = obj[static_assets.StaticBenchFactory].related_to(rooms, cu.on_floor)
    chair = obj[static_assets.StaticChairFactory].related_to(rooms, cu.on_floor)
    sofa = (
        obj[StaticVipSofaFactory]
        .related_to(rooms, cu.on_floor)
        .related_to(rooms, casework_against_wall)
    )
    lounge_table = obj[StaticLoungeTableFactory].related_to(
        rooms, cu.on_floor
    )
    front_desk = (
        obj[static_assets.StaticFronttableFactory]
        .related_to(rooms, cu.on_floor)
        .related_to(rooms, frontdesk_against_wall)
    )

    # region Waiting + reception

    constraints["waiting_room"] = waiting_room.all(
        lambda r: (
            bench.related_to(r).count().in_range(4, 6)
            * lounge_table.related_to(r).count().equals(0)
            * chair.related_to(r).count().equals(0)
        )
    )
    score_terms["waiting_room"] = waiting_room.mean(
        lambda r: (
            bench.related_to(r).mean(
                lambda b: (
                    b.distance(r, cu.walltags).hinge(0.9, 1.9).maximize(weight=7)
                    + b.distance(bench.related_to(r))
                    .hinge(0.45, 0.95)
                    .maximize(weight=8)
                    + b.distance(doors.related_to(r))
                    .hinge(1.3, 4.2)
                    .maximize(weight=4)
                    + b.distance(openings.related_to(r))
                    .hinge(0.9, 3.0)
                    .maximize(weight=7)
                    + cl.angle_alignment_cost(b, r, cu.walltags).minimize(weight=6)
                    + cl.angle_alignment_cost(b, bench.related_to(r)).minimize(weight=8)
                    + cl.accessibility_cost(b, r, dist=0.65).minimize(weight=2)
                )
            )
        )
    )

    constraints["reception"] = reception_room.all(
        lambda r: (
            front_desk.related_to(r).count().equals(1)
            * staff_chair.related_to(r).count().equals(1)
            * cabinet.related_to(r).count().in_range(0, 1)
            * chair.related_to(r).count().equals(0)
        )
    )
    score_terms["reception"] = reception_room.mean(
        lambda r: (
            front_desk.related_to(r).mean(
                lambda d: (
                    d.distance(r, cu.walltags).hinge(0.35, 0.65).minimize(weight=10)
                    + cl.angle_alignment_cost(d, r, cu.walltags).minimize(weight=6)
                    + cl.focus_score(d, openings.related_to(r)).minimize(weight=12)
                    + cl.accessibility_cost(d, r, dist=1.0).minimize(weight=6)
                    + d.distance(doors.related_to(r)).hinge(1.2, 3.0).maximize(weight=4)
                    + d.distance(windows.related_to(r)).hinge(0.6, 1.8).maximize(weight=4)
                    + d.distance(openings.related_to(r))
                    .hinge(0.8, 1.8)
                    .minimize(weight=10)
                )
            )
            + staff_chair.related_to(r).mean(
                lambda c: (
                    c.distance(front_desk.related_to(r))
                    .hinge(0.35, 0.85)
                    .maximize(weight=5)
                    + c.distance(doors.related_to(r)).hinge(0.9, 2.4).maximize(weight=2)
                )
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
            * cabinet.related_to(r).count().in_range(0, 1)
            * wall_table.related_to(r).count().in_range(1, 2)
        )
    )
    score_terms["clinic"] = clinic_room.mean(
        lambda r: (
            cl.center_stable_surface_dist(dental_unit.related_to(r)).minimize(weight=7)
            + dental_unit.related_to(r)
            .distance(r, cu.walltags)
            .hinge(0.7, 1.6)
            .maximize(weight=4)
            + cl.angle_alignment_cost(dental_unit.related_to(r), r, cu.walltags).minimize(
                weight=7
            )
            + cl.accessibility_cost(dental_unit.related_to(r), r, dist=1.1).minimize(
                weight=8
            )
            + dental_unit.related_to(r)
            .distance(doors.related_to(r))
            .hinge(1.0, 2.8)
            .maximize(weight=4)
            + staff_chair.related_to(r).mean(
                lambda s: (
                    s.distance(dental_unit.related_to(r))
                    .hinge(0.45, 0.95)
                    .maximize(weight=5)
                    + s.distance(wall_table.related_to(r))
                    .hinge(0.35, 1.1)
                    .maximize(weight=4)
                )
            )
            + washbar.related_to(r).mean(
                lambda s: (
                    s.distance(r, cu.walltags).hinge(0.08, 0.2).minimize(weight=6)
                    + cl.angle_alignment_cost(s, r, cu.walltags).minimize(weight=2)
                    + s.distance(doors.related_to(r)).hinge(0.7, 2.4).maximize(weight=2)
                    + s.distance(dental_unit.related_to(r))
                    .hinge(1.2, 2.4)
                    .maximize(weight=5)
                )
            )
            + cabinet.related_to(r).mean(
                lambda c: (
                    c.distance(r, cu.walltags).hinge(0.08, 0.22).minimize(weight=4)
                    + c.distance(doors.related_to(r)).hinge(0.7, 2.3).maximize(weight=1)
                    + c.distance(dental_unit.related_to(r))
                    .hinge(1.2, 2.6)
                    .maximize(weight=4)
                )
            )
            + wall_table.related_to(r).mean(
                lambda t: (
                    t.distance(r, cu.walltags).hinge(0.08, 0.22).minimize(weight=6)
                    + cl.angle_alignment_cost(t, r, cu.walltags).minimize(weight=2)
                    + cl.angle_alignment_cost(t, wall_table.related_to(r)).minimize(
                        weight=4
                    )
                    + t.distance(wall_table.related_to(r))
                    .hinge(0.2, 0.75)
                    .maximize(weight=4)
                    + t.distance(dental_unit.related_to(r))
                    .hinge(0.8, 1.8)
                    .maximize(weight=5)
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
            * staff_chair.related_to(r).count().in_range(1, 3)
            * cabinet.related_to(r).count().in_range(0, 1)
            * wall_table.related_to(r).count().in_range(1, 2)
            * sofa.related_to(r).count().equals(1)
            * lounge_table.related_to(r).count().equals(1)
            * chair.related_to(r).count().equals(0)
        )
    )
    score_terms["vip_clinic"] = vip_clinic.mean(
        lambda r: (
            cl.center_stable_surface_dist(dental_unit.related_to(r)).minimize(weight=6)
            + dental_unit.related_to(r)
            .distance(r, cu.walltags)
            .hinge(0.7, 1.8)
            .maximize(weight=3)
            + cl.angle_alignment_cost(dental_unit.related_to(r), r, cu.walltags).minimize(
                weight=7
            )
            + cl.accessibility_cost(dental_unit.related_to(r), r, dist=1.1).minimize(
                weight=8
            )
            + dental_unit.related_to(r)
            .distance(doors.related_to(r))
            .hinge(2.3, 5.0)
            .maximize(weight=12)
            + staff_chair.related_to(r).mean(
                lambda s: (
                    s.distance(dental_unit.related_to(r))
                    .hinge(0.45, 1.0)
                    .maximize(weight=4)
                    + s.distance(wall_table.related_to(r))
                    .hinge(0.35, 1.2)
                    .maximize(weight=4)
                    + s.distance(doors.related_to(r)).hinge(1.0, 2.8).maximize(weight=2)
                )
            )
            + washbar.related_to(r).mean(
                lambda s: (
                    s.distance(r, cu.walltags).hinge(0.08, 0.22).minimize(weight=5)
                    + cl.angle_alignment_cost(s, r, cu.walltags).minimize(weight=2)
                    + s.distance(doors.related_to(r)).hinge(1.5, 4.0).maximize(weight=4)
                    + s.distance(dental_unit.related_to(r))
                    .hinge(1.2, 2.8)
                    .maximize(weight=4)
                )
            )
            + sofa.related_to(r).mean(
                lambda s: (
                    s.distance(r, cu.walltags).hinge(0.08, 0.22).minimize(weight=3)
                    + cl.angle_alignment_cost(s, r, cu.walltags).minimize(weight=1)
                    + s.distance(doors.related_to(r)).minimize(weight=10)
                    + s.distance(dental_unit.related_to(r))
                    .hinge(3.0, 5.8)
                    .maximize(weight=7)
                )
            )
            + lounge_table.related_to(r).mean(
                lambda t: (
                    cl.angle_alignment_cost(t, r, cu.walltags).minimize(weight=1)
                    + t.distance(sofa.related_to(r)).hinge(0.6, 1.6).maximize(weight=3)
                    + t.distance(doors.related_to(r)).minimize(weight=7)
                    + t.distance(dental_unit.related_to(r))
                    .hinge(2.8, 5.2)
                    .maximize(weight=5)
                )
            )
            + cabinet.related_to(r).mean(
                lambda c: (
                    c.distance(r, cu.walltags).hinge(0.08, 0.22).minimize(weight=4)
                    + c.distance(doors.related_to(r)).hinge(1.2, 3.8).maximize(weight=3)
                    + c.distance(dental_unit.related_to(r))
                    .hinge(1.1, 2.6)
                    .maximize(weight=4)
                    + c.distance(sofa.related_to(r)).hinge(1.2, 3.0).maximize(weight=3)
                )
            )
            + wall_table.related_to(r).mean(
                lambda t: (
                    t.distance(r, cu.walltags).hinge(0.08, 0.22).minimize(weight=5)
                    + cl.angle_alignment_cost(t, r, cu.walltags).minimize(weight=1)
                    + cl.angle_alignment_cost(t, wall_table.related_to(r)).minimize(
                        weight=4
                    )
                    + t.distance(wall_table.related_to(r))
                    .hinge(0.2, 0.8)
                    .maximize(weight=4)
                    + t.distance(doors.related_to(r)).hinge(1.5, 4.0).maximize(weight=4)
                    + t.distance(sofa.related_to(r)).hinge(1.4, 3.2).maximize(weight=4)
                    + t.distance(dental_unit.related_to(r))
                    .hinge(0.8, 1.8)
                    .maximize(weight=6)
                )
            )
        )
    )

    # endregion

    # region Dental support core

    constraints["consultation_room"] = consultation_room.all(
        lambda r: (
            sink.related_to(r).count().in_range(0, 1)
            * cabinet.related_to(r).count().equals(1)
            * chair.related_to(r).count().in_range(2, 3)
            * wall_table.related_to(r).count().equals(2)
        )
    )
    constraints["sterilization_room"] = sterilization_room.all(
        lambda r: (
            sink.related_to(r).count().equals(1)
            * cabinet.related_to(r).count().in_range(1, 2)
            * staff_chair.related_to(r).count().in_range(0, 1)
            * wall_table.related_to(r).count().in_range(2, 3)
        )
    )

    score_terms["support_rooms"] = consultation_room.mean(
        lambda r: (
            wall_table.related_to(r).mean(
                lambda t: (
                    t.distance(r, cu.walltags).hinge(0.08, 0.22).minimize(weight=5)
                    + cl.angle_alignment_cost(t, r, cu.walltags).minimize(weight=3)
                    + cl.angle_alignment_cost(t, wall_table.related_to(r)).minimize(
                        weight=5
                    )
                    + t.distance(wall_table.related_to(r))
                    .hinge(0.18, 0.55)
                    .maximize(weight=5)
                    + t.distance(doors.related_to(r)).hinge(0.8, 2.2).maximize(weight=2)
                )
            )
            + chair.related_to(r).mean(
                lambda c: c.distance(wall_table.related_to(r))
                .hinge(0.55, 1.2)
                .maximize(weight=3)
            )
            + cabinet.related_to(r).mean(
                lambda c: (
                    c.distance(r, cu.walltags).hinge(0.08, 0.22).minimize(weight=3)
                    + c.distance(wall_table.related_to(r))
                    .hinge(0.3, 1.1)
                    .maximize(weight=2)
                )
            )
        )
    ) + sterilization_room.mean(
        lambda r: (
            wall_table.related_to(r).mean(
                lambda t: (
                    t.distance(r, cu.walltags).hinge(0.08, 0.22).minimize(weight=5)
                    + cl.angle_alignment_cost(t, r, cu.walltags).minimize(weight=3)
                    + cl.angle_alignment_cost(t, wall_table.related_to(r)).minimize(
                        weight=5
                    )
                    + t.distance(wall_table.related_to(r))
                    .hinge(0.18, 0.55)
                    .maximize(weight=5)
                    + t.distance(doors.related_to(r)).hinge(0.8, 2.0).maximize(weight=2)
                )
            )
            + sink.related_to(r).mean(
                lambda s: s.distance(cabinet.related_to(r))
                .hinge(0.4, 1.6)
                .maximize(weight=2)
            )
            + cabinet.related_to(r).mean(
                lambda c: (
                    c.distance(r, cu.walltags).hinge(0.08, 0.22).minimize(weight=3)
                    + c.distance(wall_table.related_to(r))
                    .hinge(0.3, 1.4)
                    .maximize(weight=2)
                )
            )
        )
    )

    # endregion

    constraints["corridor"] = corridor.all(
        lambda r: furniture.related_to(r).count().equals(0)
    )

    return cl.Problem(constraints=constraints, score_terms=score_terms)
