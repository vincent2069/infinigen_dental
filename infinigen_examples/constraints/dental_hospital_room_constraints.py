# Copyright (C) 2023, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory
# of this source tree.

# Authors: Dental hospital room setup for predefined floor plans

from collections import OrderedDict

import gin

from infinigen.core.constraints import constraint_language as cl
from infinigen.core.constraints.constraint_language.constants import RoomConstants
from infinigen.core.tags import Semantics


@gin.configurable
def dental_hospital_room_constraints():
    """Room problem used together with a predefined/programmatic floor plan.

    The predefined floor-plan solver does not sample a room graph from these
    constraints; it mainly needs the room constants. We still register the room
    types here so the configuration is explicit and consistent with the dental
    hospital scene.
    """

    constants = RoomConstants(
        fixed_contour=True,
        room_type={
            Semantics.HospitalWaitingRoom,
            Semantics.HospitalReception,
            Semantics.HospitalClinic,
            Semantics.HospitalVIPClinic,
            Semantics.HospitalVIPLounge,
            Semantics.HospitalVIPTreatment,
            Semantics.HospitalCorridor,
            Semantics.HospitalTreatmentRoom,
            Semantics.HospitalExaminationRoom,
        },
    )

    return cl.Problem(
        constraints=OrderedDict(),
        score_terms=OrderedDict(),
        constants=constants,
    )
