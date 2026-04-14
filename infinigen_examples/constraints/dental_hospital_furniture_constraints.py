# Copyright (C) 2023, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory
# of this source tree.

# Authors: Dental hospital furniture constraints for large clinic scenes

from collections import OrderedDict

import infinigen.assets.static_assets as static_assets
from infinigen.assets.objects import lamp
from infinigen.core.constraints import constraint_language as cl
from infinigen.core.constraints import usage_lookup
from infinigen.core.tags import Semantics

from . import util as cu
from .dental_hospital_semantics import (
    StaticWashbarFactory,
    dental_hospital_asset_usage,
)


def dental_hospital_furniture_constraints():
    """Construct furniture constraints for a large dental hospital.

    Notes for the dental preset:
    - ``HospitalExaminationRoom`` is interpreted as a consultation / imaging
      support room near the clinical core.
    - ``HospitalTreatmentRoom`` is interpreted as a sterilization / staff-
      support room.
    - Main clinical operatories remain ``HospitalClinic`` and
      ``HospitalVIPClinic``; every such operatory must contain exactly one
      dental unit and one wall-side washbar / sink station.
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
    bench = (
        obj[static_assets.StaticBenchFactory]
        .related_to(rooms, cu.on_floor)
        .related_to(rooms, cu.against_wall)
    )
    chair = obj[static_assets.StaticChairFactory].related_to(rooms, cu.on_floor)
    sofa = (
        obj[static_assets.StaticSofaFactory]
        .related_to(rooms, cu.on_floor)
        .related_to(rooms, cu.against_wall)
    )
    lounge_table = obj[static_assets.StaticRectangleFactory].related_to(
        rooms, cu.on_floor
    )
    front_desk = obj[static_assets.StaticFronttableFactory].related_to(
        rooms, cu.on_floor
    )
    ceiling_light = obj[lamp.CeilingLightFactory].related_to(rooms, cu.hanging)

    # region Waiting + reception

    constraints["waiting_room"] = waiting_room.all(
        lambda r: (
            bench.related_to(r).count().in_range(4, 10)
            * chair.related_to(r).count().in_range(2, 6)
            * table.related_to(r).count().in_range(1, 2)
            * table.related_to(r).all(
                lambda t: chair.related_to(r)
                .related_to(t, cu.front_against)
                .count()
                .in_range(2, 4)
            )
        )
    )
    score_terms["waiting_room"] = waiting_room.mean(
        lambda r: (
            table.related_to(r)
            .mean(
                lambda t: (
                    t.distance(r, cu.walltags).hinge(0.6, 1.8).maximize(weight=2)
                    + cl.angle_alignment_cost(t, r, cu.walltags).minimize(weight=2)
                    + t.distance(table.related_to(r))
                    .hinge(1.2, 2.4)
                    .maximize(weight=1.5)
                )
            )
            + bench.related_to(r)
            .mean(
                lambda b: (
                    b.distance(table.related_to(r))
                    .hinge(2.0, 5.0)
                    .maximize(weight=5)
                    + b.distance(bench.related_to(r))
                    .hinge(0.9, 2.0)
                    .maximize(weight=2)
                    + cl.angle_alignment_cost(b, r, cu.walltags).minimize(weight=3)
                )
            )
            + chair.related_to(r)
            .mean(
                lambda c: (
                    c.distance(table.related_to(r))
                    .hinge(0.6, 1.4)
                    .maximize(weight=3)
                    + c.distance(bench.related_to(r))
                    .hinge(1.4, 3.2)
                    .maximize(weight=3)
                    + c.distance(chair.related_to(r))
                    .hinge(0.45, 0.95)
                    .maximize(weight=1)
                )
            )
        )
    )

    constraints["reception"] = reception_room.all(
        lambda r: (
            front_desk.related_to(r).count().equals(1)
            * staff_chair.related_to(r).count().in_range(2, 3)
            * chair.related_to(r).count().in_range(0, 1)
            * cabinet.related_to(r).count().in_range(0, 1)
        )
    )
    score_terms["reception"] = reception_room.mean(
        lambda r: (
            front_desk.related_to(r).mean(
                lambda d: (
                    cl.center_stable_surface_dist(d).minimize(weight=7)
                    + d.distance(r, cu.walltags).hinge(0.7, 2.1).maximize(weight=4)
                    + cl.angle_alignment_cost(d, r, cu.walltags).minimize(weight=2)
                    + cl.accessibility_cost(d, r, dist=1.6).minimize(weight=8)
                    + d.distance(doors.related_to(r)).hinge(1.0, 3.0).maximize(weight=1)
                )
            )
            + staff_chair.related_to(r).mean(
                lambda c: (
                    c.distance(front_desk.related_to(r))
                    .hinge(0.5, 1.3)
                    .maximize(weight=3)
                    + c.distance(staff_chair.related_to(r))
                    .hinge(0.35, 0.9)
                    .maximize(weight=1)
                )
            )
            + chair.related_to(r).mean(
                lambda c: c.distance(front_desk.related_to(r))
                .hinge(1.2, 2.4)
                .maximize(weight=2)
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
            * sink.related_to(r).count().equals(1)
            * staff_chair.related_to(r).count().in_range(1, 2)
            * cabinet.related_to(r).count().in_range(1, 4)
            * wall_table.related_to(r).count().in_range(1, 2)
        )
    )
    score_terms["clinic"] = clinic_room.mean(
        lambda r: (
            cl.center_stable_surface_dist(dental_unit.related_to(r)).minimize(weight=4)
            + cl.angle_alignment_cost(dental_unit.related_to(r), r, cu.walltags).minimize(
                weight=2
            )
            + cl.accessibility_cost(dental_unit.related_to(r), r, dist=1.0).minimize(
                weight=5
            )
            + cl.accessibility_cost(
                dental_unit.related_to(r), furniture.related_to(r), dist=1.2
            ).minimize(weight=4)
            + (
                (cabinet.related_to(r).count() + wall_table.related_to(r).count())
                / r.volume(dims=2)
            ).hinge(0.08, 0.16).minimize(weight=3)
            + staff_chair.related_to(r)
            .mean(
                lambda s: s.distance(dental_unit.related_to(r))
                .hinge(0.7, 1.8)
                .maximize(weight=2)
            )
            + washbar.related_to(r).mean(
                lambda s: (
                    cl.angle_alignment_cost(s, r, cu.walltags).minimize(weight=1)
                    + s.distance(doors.related_to(r)).hinge(0.6, 2.0).maximize(weight=1)
                    + s.distance(dental_unit.related_to(r))
                    .hinge(1.5, 3.2)
                    .maximize(weight=1)
                )
            )
            + cabinet.related_to(r).mean(
                lambda c: (
                    cl.angle_alignment_cost(c, r, cu.walltags).minimize(weight=1)
                    + c.distance(r, cu.walltags).maximize(weight=1)
                    + c.distance(dental_unit.related_to(r))
                    .hinge(1.4, 3.4)
                    .maximize(weight=3)
                    + c.distance(wall_table.related_to(r))
                    .hinge(0.3, 1.5)
                    .maximize(weight=2)
                )
            )
            + wall_table.related_to(r).mean(
                lambda t: (
                    cl.angle_alignment_cost(t, r, cu.walltags).minimize(weight=1)
                    + t.distance(dental_unit.related_to(r))
                    .hinge(1.5, 3.2)
                    .maximize(weight=3)
                    + t.distance(cabinet.related_to(r))
                    .hinge(0.3, 1.5)
                    .maximize(weight=2)
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
            * sink.related_to(r).count().equals(1)
            * staff_chair.related_to(r).count().in_range(2, 3)
            * cabinet.related_to(r).count().in_range(2, 5)
            * wall_table.related_to(r).count().in_range(1, 2)
            * sofa.related_to(r).count().equals(1)
            * lounge_table.related_to(r).count().equals(1)
            * chair.related_to(r).count().in_range(0, 2)
        )
    )
    score_terms["vip_clinic"] = vip_clinic.mean(
        lambda r: (
            cl.center_stable_surface_dist(dental_unit.related_to(r)).minimize(weight=3)
            + cl.angle_alignment_cost(dental_unit.related_to(r), r, cu.walltags).minimize(
                weight=2
            )
            + cl.accessibility_cost(dental_unit.related_to(r), r, dist=1.1).minimize(
                weight=5
            )
            + cl.accessibility_cost(
                dental_unit.related_to(r), furniture.related_to(r), dist=1.2
            ).minimize(weight=4)
            + (
                (cabinet.related_to(r).count() + wall_table.related_to(r).count())
                / r.volume(dims=2)
            ).hinge(0.09, 0.18).minimize(weight=3)
            + washbar.related_to(r).mean(
                lambda s: (
                    cl.angle_alignment_cost(s, r, cu.walltags).minimize(weight=1)
                    + s.distance(dental_unit.related_to(r))
                    .hinge(1.6, 3.4)
                    .maximize(weight=2)
                )
            )
            + sofa.related_to(r)
            .mean(
                lambda s: (
                    cl.angle_alignment_cost(s, r, cu.walltags).minimize(weight=1)
                    + s.distance(dental_unit.related_to(r))
                    .hinge(2.8, 6.0)
                    .maximize(weight=5)
                )
            )
            + lounge_table.related_to(r)
            .mean(
                lambda t: (
                    cl.angle_alignment_cost(t, r, cu.walltags).minimize(weight=1)
                    + t.distance(sofa.related_to(r))
                    .hinge(0.6, 1.8)
                    .maximize(weight=3)
                    + t.distance(dental_unit.related_to(r))
                    .hinge(2.8, 6.0)
                    .maximize(weight=4)
                )
            )
            + chair.related_to(r).mean(
                lambda c: (
                    c.distance(lounge_table.related_to(r))
                    .hinge(0.6, 1.6)
                    .maximize(weight=2)
                    + c.distance(dental_unit.related_to(r))
                    .hinge(2.4, 5.0)
                    .maximize(weight=2)
                )
            )
            + cabinet.related_to(r).mean(
                lambda c: (
                    cl.angle_alignment_cost(c, r, cu.walltags).minimize(weight=1)
                    + c.distance(dental_unit.related_to(r))
                    .hinge(1.6, 3.8)
                    .maximize(weight=3)
                    + c.distance(wall_table.related_to(r))
                    .hinge(0.3, 1.5)
                    .maximize(weight=2)
                )
            )
            + wall_table.related_to(r).mean(
                lambda t: (
                    cl.angle_alignment_cost(t, r, cu.walltags).minimize(weight=1)
                    + t.distance(cabinet.related_to(r))
                    .hinge(0.3, 1.5)
                    .maximize(weight=2)
                    + t.distance(dental_unit.related_to(r))
                    .hinge(1.6, 3.4)
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
            * table.related_to(r).count().equals(1)
        )
    )
    constraints["sterilization_room"] = sterilization_room.all(
        lambda r: (
            sink.related_to(r).count().in_range(1, 2)
            * cabinet.related_to(r).count().in_range(2, 4)
            * staff_chair.related_to(r).count().in_range(0, 1)
            * table.related_to(r).count().in_range(1, 2)
        )
    )

    score_terms["support_rooms"] = consultation_room.mean(
        lambda r: (
            chair.related_to(r)
            .mean(
                lambda c: c.distance(table.related_to(r))
                .hinge(0.6, 1.8)
                .maximize(weight=2)
            )
            + cabinet.related_to(r).mean(
                lambda c: c.distance(doors.related_to(r)).maximize(weight=1)
            )
        )
    ) + sterilization_room.mean(
        lambda r: (
            sink.related_to(r)
            .mean(
                lambda s: s.distance(cabinet.related_to(r))
                .hinge(0.4, 1.8)
                .maximize(weight=2)
            )
            + cabinet.related_to(r)
            .mean(
                lambda c: c.distance(table.related_to(r))
                .hinge(0.5, 2.2)
                .maximize(weight=1)
            )
        )
    )

    # endregion

    # region Ceiling lights

    constraints["ceiling_lights"] = (
        waiting_room.all(lambda r: ceiling_light.related_to(r).count().in_range(2, 8))
        * reception_room.all(
            lambda r: ceiling_light.related_to(r).count().in_range(1, 4)
        )
        * clinic_room.all(lambda r: ceiling_light.related_to(r).count().in_range(1, 3))
        * vip_clinic.all(lambda r: ceiling_light.related_to(r).count().in_range(2, 4))
        * consultation_room.all(
            lambda r: ceiling_light.related_to(r).count().in_range(1, 3)
        )
        * sterilization_room.all(
            lambda r: ceiling_light.related_to(r).count().in_range(1, 3)
        )
        * corridor.all(lambda r: ceiling_light.related_to(r).count().in_range(1, 8))
    )

    def room_light_score(roomset, density_lo=0.08, density_hi=0.12):
        return roomset.mean(
            lambda r: (
                (
                    ceiling_light.related_to(r).count() / r.volume(dims=2)
                ).hinge(density_lo, density_hi).minimize(weight=7)
                + cl.angle_alignment_cost(
                    ceiling_light.related_to(r), r, cu.walltags
                ).minimize(weight=1)
                + ceiling_light.related_to(r)
                .mean(
                    lambda l: (
                        l.distance(r, cu.walltags).pow(0.5) * 1.4
                        + l.distance(ceiling_light.related_to(r)).pow(0.25) * 2.4
                    )
                )
                .maximize(weight=1)
            )
        )

    score_terms["ceiling_lights"] = (
        room_light_score(waiting_room)
        + room_light_score(reception_room)
        + room_light_score(clinic_room)
        + room_light_score(vip_clinic)
        + room_light_score(consultation_room)
        + room_light_score(sterilization_room)
        + room_light_score(corridor, density_lo=0.05, density_hi=0.10)
    )

    # endregion

    # Corridors should remain visually and physically clear.
    constraints["corridor"] = corridor.all(
        lambda r: furniture.related_to(r).count().equals(0)
    )

    return cl.Problem(constraints=constraints, score_terms=score_terms)
