# Copyright (C) 2023, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory
# of this source tree.

# Authors: Hospital room constraints for generating large hospital environments

from collections import OrderedDict

import gin
import numpy as np
from numpy.random import uniform

from infinigen.core.constraints import constraint_language as cl
from infinigen.core.constraints.constraint_language.constants import RoomConstants
from infinigen.core.constraints.constraint_language import rooms  # noqa: F401 - needed for registering room methods
from infinigen.core.tags import Semantics


@gin.configurable
def hospital_room_constraints(
    num_clinics: int = 15,  # Total number of clinics (普通 + VIP)
    num_vip_clinics: int = 3,  # Number of VIP clinics within total
    has_large_waiting_room: bool = True,
):
    """
    Construct a constraint graph for hospital room layouts.

    Hospital layout structure:
    - 等候区 (Waiting Room): Large central area for patients to wait
    - 导诊区 (Reception): Information desk area near entrance
    - 治疗区 (Treatment Zone): Multiple clinics arranged along corridors
      - 普通诊室 (Standard Clinic): 10-20 rooms
      - VIP 诊室 (VIP Clinic): Premium rooms

    Rooms are arranged in 2-3 rows along corridors for organized layout.

    Args:
        num_clinics: Total number of clinic rooms (standard + VIP)
        num_vip_clinics: Number of VIP clinics (subset of total)
        has_large_waiting_room: Whether to create a large central waiting area
    """
    constraints = OrderedDict()
    score_terms = OrderedDict()

    constants = RoomConstants(fixed_contour=False)
    rooms = cl.scene()[Semantics.RoomContour]

    # Hospital room type aliases
    waiting = rooms[Semantics.HospitalWaitingRoom]
    reception = rooms[Semantics.HospitalReception]
    clinic = rooms[Semantics.HospitalClinic]
    vip_clinic = rooms[Semantics.HospitalVIPClinic]
    corridor = rooms[Semantics.HospitalCorridor]
    treatment = rooms[Semantics.HospitalTreatmentRoom]

    # region ROOM SCENE GRAPH CONSTRAINTS

    # Root should connect to entrance/waiting room
    constraints["room_generation"] = (
        # Main waiting room connected to root/entrance
        rooms[Semantics.Root].all(
            lambda r: waiting.related_to(r, cl.Traverse()).count().in_range(1, 2)
        )
        # Reception near waiting room
        * waiting.all(
            lambda r: reception.related_to(r, cl.Traverse()).count().in_range(0, 2)
        )
        # Corridors connect to waiting room
        * waiting.all(
            lambda r: corridor.related_to(r, cl.Traverse()).count().in_range(1, 3)
        )
        # Clinics connect to corridors
        * corridor.all(
            lambda r: clinic.related_to(r, cl.Traverse()).count().in_range(3, 10)
        )
        * corridor.all(
            lambda r: vip_clinic.related_to(r, cl.Traverse()).count().in_range(0, 5)
        )
        # Total clinic count constraints
        * rooms.all(
            lambda r: clinic.count().in_range(
                num_clinics - num_vip_clinics - 2, num_clinics - num_vip_clinics + 2
            )
        )
        * rooms.all(
            lambda r: vip_clinic.count().in_range(
                num_vip_clinics - 1, num_vip_clinics + 1
            )
        )
        # Treatment rooms (specialized)
        * corridor.all(
            lambda r: treatment.related_to(r, cl.Traverse()).count().in_range(0, 3)
        )
    )

    # endregion

    # region ROOM SCORING TERMS

    def exterior(r):
        return r.same_level()[Semantics.Exterior]

    # Room size preferences
    room_term = (
        # Large waiting room for many patients
        waiting.sum(
            lambda r: (r.area() / 100).log().hinge(0, 0.4).pow(2)
        ).minimize(weight=500.0)
        # Medium reception area
        + reception.sum(
            lambda r: (r.area() / 30).log().hinge(0, 0.4).pow(2)
        ).minimize(weight=400.0)
        # Standard clinic size (smaller, efficient)
        + clinic.sum(
            lambda r: (r.area() / 20).log().hinge(0, 0.4).pow(2)
        ).minimize(weight=400.0)
        # VIP clinics slightly larger
        + vip_clinic.sum(
            lambda r: (r.area() / 30).log().hinge(0, 0.4).pow(2)
        ).minimize(weight=400.0)
        # Corridors should be long and narrow
        + corridor.sum(
            lambda r: (r.area() / 50).log().hinge(0, 0.4).pow(2)
        ).minimize(weight=300.0)
        # Treatment rooms medium sized
        + treatment.sum(
            lambda r: (r.area() / 25).log().hinge(0, 0.4).pow(2)
        ).minimize(weight=400.0)
        # Encourage rectangular rooms for organized layout
        + sum(
            rooms[tag].sum(lambda r: r.aspect_ratio().log())
            for tag in [
                Semantics.HospitalClinic,
                Semantics.HospitalVIPClinic,
                Semantics.HospitalCorridor,
            ]
        ).minimize(weight=50.0)
        # Clinics should have good access to corridors
        + sum(
            rooms[tag].sum(lambda r: r.shared_length(corridor) / r.length())
            for tag in [Semantics.HospitalClinic, Semantics.HospitalVIPClinic]
        ).maximize(weight=20.0)
        # Minimize narrow rooms (except corridors)
        + rooms[
            -Semantics.HospitalCorridor
        ].sum(lambda r: r.narrowness(constants, 2.5)).minimize(weight=2000.0)
        + corridor.sum(lambda r: r.narrowness(constants, 1.5)).minimize(weight=500.0)
    )

    score_terms["room"] = room_term

    # endregion

    return cl.Problem(
        constraints=constraints, score_terms=score_terms, constants=constants
    )
