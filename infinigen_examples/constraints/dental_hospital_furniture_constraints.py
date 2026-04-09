# Copyright (C) 2023, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory
# of this source tree.

# Authors: Dental hospital furniture constraints for large clinic scenes

from collections import OrderedDict

import infinigen.assets.static_assets as static_assets
from infinigen.core.constraints import constraint_language as cl
from infinigen.core.constraints import usage_lookup
from infinigen.core.tags import Semantics

from . import util as cu
from .dental_hospital_semantics import dental_hospital_asset_usage


def dental_hospital_furniture_constraints():
    """Construct furniture constraints for a large dental hospital.

    Notes for the dental preset:
    - ``HospitalExaminationRoom`` is interpreted as a consultation / imaging
      support room near the clinical core.
    - ``HospitalTreatmentRoom`` is interpreted as a sterilization / staff-
      support room.
    - Main clinical operatories remain ``HospitalClinic`` and
      ``HospitalVIPClinic``; every such operatory must contain exactly one
      dental unit and one sink.
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
    sink = obj[Semantics.Sink].related_to(rooms, cu.against_wall)
    staff_chair = obj[static_assets.StaticInternchairFactory].related_to(
        rooms, cu.on_floor
    )
    cabinet = obj[static_assets.StaticCabinetFactory].related_to(rooms, cu.against_wall)
    table = obj[static_assets.StaticTableFactory].related_to(rooms, cu.on_floor)
    bench = obj[static_assets.StaticBenchFactory].related_to(rooms, cu.against_wall)
    chair = obj[static_assets.StaticChairFactory].related_to(rooms, cu.on_floor)
    sofa = obj[static_assets.StaticSofaFactory].related_to(rooms, cu.against_wall)
    front_desk = obj[static_assets.StaticFronttableFactory].related_to(
        rooms, cu.against_wall
    )

    # region Waiting + reception

    constraints["waiting_room"] = waiting_room.all(
        lambda r: (
            bench.related_to(r).count().in_range(2, 6)
            * chair.related_to(r).count().in_range(2, 8)
            * table.related_to(r).count().in_range(1, 2)
        )
    )
    score_terms["waiting_room"] = waiting_room.mean(
        lambda r: (
            cl.center_stable_surface_dist(table.related_to(r)).minimize(weight=2)
            + chair.related_to(r)
            .mean(
                lambda c: c.distance(table.related_to(r))
                .hinge(0.8, 2.2)
                .maximize(weight=1)
            )
        )
    )

    constraints["reception"] = reception_room.all(
        lambda r: (
            front_desk.related_to(r).count().equals(1)
            * staff_chair.related_to(r).count().in_range(1, 2)
            * chair.related_to(r).count().in_range(1, 4)
            * cabinet.related_to(r).count().in_range(0, 1)
        )
    )
    score_terms["reception"] = reception_room.mean(
        lambda r: (
            front_desk.related_to(r).mean(
                lambda d: d.distance(doors.related_to(r)).minimize(weight=5)
            )
        )
    )

    # endregion

    # region Standard clinics

    constraints["clinic"] = clinic_room.all(
        lambda r: (
            dental_unit.related_to(r).count().equals(1)
            * sink.related_to(r).count().equals(1)
            * staff_chair.related_to(r).count().in_range(1, 2)
            * cabinet.related_to(r).count().in_range(1, 2)
            * table.related_to(r).count().in_range(0, 1)
        )
    )
    score_terms["clinic"] = clinic_room.mean(
        lambda r: (
            cl.center_stable_surface_dist(dental_unit.related_to(r)).minimize(weight=4)
            + staff_chair.related_to(r)
            .mean(
                lambda s: s.distance(dental_unit.related_to(r))
                .hinge(0.7, 1.8)
                .maximize(weight=2)
            )
            + sink.related_to(r).mean(
                lambda s: s.distance(doors.related_to(r)).maximize(weight=1)
            )
        )
    )

    # endregion

    # region VIP clinics with lounge area

    constraints["vip_clinic"] = vip_clinic.all(
        lambda r: (
            dental_unit.related_to(r).count().equals(1)
            * sink.related_to(r).count().equals(1)
            * staff_chair.related_to(r).count().in_range(2, 3)
            * cabinet.related_to(r).count().in_range(1, 3)
            * sofa.related_to(r).count().equals(1)
            * table.related_to(r).count().in_range(1, 2)
        )
    )
    score_terms["vip_clinic"] = vip_clinic.mean(
        lambda r: (
            cl.center_stable_surface_dist(dental_unit.related_to(r)).minimize(weight=3)
            + sofa.related_to(r)
            .mean(
                lambda s: s.distance(dental_unit.related_to(r))
                .hinge(2.2, 4.8)
                .maximize(weight=4)
            )
            + table.related_to(r)
            .mean(
                lambda t: t.distance(sofa.related_to(r))
                .hinge(0.6, 1.8)
                .maximize(weight=3)
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

    # Corridors should remain visually and physically clear.
    constraints["corridor"] = corridor.all(
        lambda r: furniture.related_to(r).count().equals(0)
    )

    return cl.Problem(constraints=constraints, score_terms=score_terms)
