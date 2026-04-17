# Copyright (C) 2023, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory
# of this source tree.

# Authors: Programmatic dental hospital floor plan for large outpatient scenes

import gin
import numpy as np
import shapely
from shapely import LineString

from infinigen.core.constraints.example_solver.room.base import room_name
from infinigen.core.tags import Semantics
from infinigen.core.util.math import FixedSeed


def _split_even(total: int) -> tuple[int, int]:
    return (total + 1) // 2, total // 2


def _balanced_standard_split(
    standard_rooms: int,
    top_vip_rooms: int,
    bottom_vip_rooms: int,
    standard_width: float,
    vip_width: float,
) -> tuple[int, int]:
    best_top = 0
    best_key = None

    for top_standard in range(standard_rooms + 1):
        bottom_standard = standard_rooms - top_standard
        if top_standard == 0 or bottom_standard == 0:
            continue

        top_span = top_standard * standard_width
        bottom_span = bottom_standard * standard_width
        top_span += top_vip_rooms * vip_width
        bottom_span += bottom_vip_rooms * vip_width

        key = (
            abs(top_span - bottom_span),
            abs(top_standard - bottom_standard),
        )
        if best_key is None or key < best_key:
            best_key = key
            best_top = top_standard

    if best_key is None:
        return _split_even(standard_rooms)
    return best_top, standard_rooms - best_top


def _allocate_standard_counts(
    standard_rooms: int,
    base_widths: list[float],
    standard_width: float,
) -> list[int]:
    counts = [0] * len(base_widths)
    curr_widths = list(base_widths)

    for _ in range(standard_rooms):
        idx = min(range(len(curr_widths)), key=lambda i: (curr_widths[i], counts[i], i))
        counts[idx] += 1
        curr_widths[idx] += standard_width

    return counts


def _resolve_room_size(
    width: float,
    depth: float,
    area: float | None,
    aspect_ratio: float,
) -> tuple[float, float]:
    if area is None:
        return width, depth

    area = float(area)
    aspect_ratio = float(aspect_ratio)
    if area <= 0:
        raise ValueError(f"Room area must be positive, got {area}")
    if aspect_ratio <= 0:
        raise ValueError(f"Aspect ratio must be positive, got {aspect_ratio}")

    resolved_width = float(np.sqrt(area * aspect_ratio))
    resolved_depth = area / resolved_width
    return resolved_width, resolved_depth


def _resolve_corridor_width(
    corridor_width: float | None,
    corridor_width_min: float | None,
    corridor_width_max: float | None,
) -> float:
    if corridor_width is not None:
        resolved_width = float(corridor_width)
    else:
        low = 1.0 if corridor_width_min is None else float(corridor_width_min)
        high = 1.5 if corridor_width_max is None else float(corridor_width_max)
        if low <= 0 or high <= 0:
            raise ValueError(
                f"Corridor width bounds must be positive, got {corridor_width_min=}, {corridor_width_max=}"
            )
        if high < low:
            raise ValueError(
                f"corridor_width_max must be >= corridor_width_min, got {corridor_width_min=}, {corridor_width_max=}"
            )
        resolved_width = float(np.random.uniform(low, high))

    if resolved_width <= 0:
        raise ValueError(f"corridor_width must be positive, got {resolved_width}")
    return resolved_width


def _horizontal_segment(x0: float, x1: float, y: float, width: float) -> LineString:
    span = max(1.2, min(width, x1 - x0 - 0.6))
    span = min(span, x1 - x0 - 0.2)
    cx = (x0 + x1) / 2
    half = span / 2
    return LineString([(cx - half, y), (cx + half, y)])


def _horizontal_segment_biased(
    x0: float,
    x1: float,
    y: float,
    width: float,
    side: str = "center",
    inset: float = 0.35,
) -> LineString:
    span = max(1.2, min(width, x1 - x0 - 0.6))
    span = min(span, x1 - x0 - 0.2)
    if side == "start":
        start = min(x0 + inset, x1 - span - 0.1)
        start = max(start, x0 + 0.1)
        return LineString([(start, y), (start + span, y)])
    if side == "end":
        end = max(x1 - inset, x0 + span + 0.1)
        end = min(end, x1 - 0.1)
        return LineString([(end - span, y), (end, y)])
    return _horizontal_segment(x0, x1, y, width)


def _vertical_segment(y0: float, y1: float, x: float, width: float) -> LineString:
    span = max(1.2, min(width, y1 - y0 - 0.6))
    span = min(span, y1 - y0 - 0.2)
    cy = (y0 + y1) / 2
    half = span / 2
    return LineString([(x, cy - half), (x, cy + half)])


@gin.configurable
def dental_hospital_floorplan(
    factory_seed: int,
    num_clinics: int = 12,
    vip_ratio: float = 0.25,
    corridor_width: float | None = None,
    corridor_width_min: float = 1.0,
    corridor_width_max: float = 1.5,
    standard_clinic_width: float = 4.6,
    standard_clinic_depth: float = 5.0,
    standard_clinic_area: float | None = 23.0,
    standard_clinic_aspect_ratio: float = 0.8,
    vip_clinic_width: float = 5.8,
    vip_clinic_depth: float = 6.0,
    vip_clinic_area: float | None = 34.8,
    vip_clinic_aspect_ratio: float = 0.84,
    lobby_width: float = 10.5,
    waiting_depth: float = 7.8,
    reception_depth: float = 5.8,
    public_zone_depth: float | None = 6.9,
    reception_width_ratio: float = 0.26,
    front_buffer_length: float = 0.0,
    support_room_width: float = 5.8,
    treatment_depth: float = 5.8,
    examination_depth: float = 5.2,
    wing_standard_ratio: float = 0.0,
    corridor_connector_length: float = 4.0,
    interior_door_width: float = 1.5,
    entrance_width: float = 2.2,
    public_corridor_entry_count: int = 1,
    public_zone_open_width: float = 6.0,
    dual_corridor_threshold: int = 17,
    triple_corridor_threshold: int = 27,
    multi_corridor_threshold: int | None = None,
    four_row_threshold: int | None = None,
    add_exterior_windows: bool = True,
    vip_cluster_side: str = "split",
    vip_at_far_end: bool = True,
    plan_form: str = "rectangular",
):
    """Generate a compact dental hospital floor plan.

    Supported plan forms:
    - ``rectangular``: default. A side public-zone block plus a main clinical
      trunk corridor. Waiting/reception stay visually open, then connect into
      the treatment corridor through one or two controlled entries. When the
      clinic count exceeds 16, rectangular mode automatically switches to a
      dual-corridor variant; when it exceeds 26, it upgrades again to a
      triple-corridor / four-row clinic block.
    - ``t_shape``: public front zone -> short buffer/stem -> shared split -> upper/lower
      clinic wings.
    """

    with FixedSeed(factory_seed):
        num_clinics = int(np.clip(num_clinics, 5, 30))
        num_vip = int(round(num_clinics * vip_ratio))
        num_vip = max(1, min(num_clinics - 1, num_vip))
        num_standard = num_clinics - num_vip

        standard_clinic_width, standard_clinic_depth = _resolve_room_size(
            standard_clinic_width,
            standard_clinic_depth,
            standard_clinic_area,
            standard_clinic_aspect_ratio,
        )
        corridor_width = _resolve_corridor_width(
            corridor_width,
            corridor_width_min,
            corridor_width_max,
        )
        vip_clinic_width, vip_clinic_depth = _resolve_room_size(
            vip_clinic_width,
            vip_clinic_depth,
            vip_clinic_area,
            vip_clinic_aspect_ratio,
        )

        if public_zone_depth is not None:
            public_zone_depth = float(public_zone_depth)
            if public_zone_depth <= 0:
                raise ValueError(
                    f"public_zone_depth must be positive, got {public_zone_depth}"
                )
            waiting_depth = public_zone_depth
            reception_depth = public_zone_depth

        vip_cluster_side = vip_cluster_side.lower()
        if vip_cluster_side not in {"top", "bottom", "split"}:
            raise ValueError(
                f"Unsupported {vip_cluster_side=}, expected 'top', 'bottom' or 'split'"
            )

        plan_form = plan_form.lower()
        if plan_form not in {"t_shape", "rectangular"}:
            raise ValueError(
                f"Unsupported {plan_form=}, expected 't_shape' or 'rectangular'"
            )

        wing_standard_ratio = float(np.clip(wing_standard_ratio, 0.0, 0.6))
        corridor_connector_length = max(float(corridor_connector_length), corridor_width)
        front_buffer_length = max(float(front_buffer_length), 0.0)

        if vip_cluster_side == "top":
            top_vip_total, bottom_vip_total = num_vip, 0
        elif vip_cluster_side == "bottom":
            top_vip_total, bottom_vip_total = 0, num_vip
        else:
            top_vip_total, bottom_vip_total = _split_even(num_vip)

        top_standard_total, bottom_standard_total = _balanced_standard_split(
            num_standard,
            top_vip_total,
            bottom_vip_total,
            standard_clinic_width,
            vip_clinic_width,
        )
        shared_front_capacity = min(top_standard_total, bottom_standard_total)
        if shared_front_capacity >= 2:
            shared_front_standard = int(
                round(shared_front_capacity * (1.0 - wing_standard_ratio))
            )
            shared_front_standard = min(
                max(shared_front_standard, 1), shared_front_capacity
            )
        else:
            shared_front_standard = shared_front_capacity

        rooms = {}
        doors = {}
        windows = {}
        entrance = {}
        opens = {}

        clinic_idx = 0
        vip_idx = 0

        corridor_name = room_name(Semantics.HospitalCorridor, 0, 0)
        waiting_name = room_name(Semantics.HospitalWaitingRoom, 0, 0)
        reception_name = room_name(Semantics.HospitalReception, 0, 0)

        def add_room_windows(prefix: str, x0: float, x1: float, y: float):
            if not add_exterior_windows:
                return
            window_width = max(2.0, min((x1 - x0) * 0.45, 4.5))
            windows[prefix] = {
                "shape": _horizontal_segment(x0, x1, y, window_width),
            }

        def add_room_windows_vertical(prefix: str, y0: float, y1: float, x: float):
            if not add_exterior_windows:
                return
            window_width = max(1.5, min((y1 - y0) * 0.4, 3.5))
            windows[prefix] = {
                "shape": _vertical_segment(y0, y1, x, window_width),
            }

        def room_dims(semantic: Semantics) -> tuple[float, float]:
            if semantic == Semantics.HospitalVIPClinic:
                return vip_clinic_width, vip_clinic_depth
            if semantic == Semantics.HospitalClinic:
                return standard_clinic_width, standard_clinic_depth
            if semantic == Semantics.HospitalExaminationRoom:
                return support_room_width, examination_depth
            if semantic == Semantics.HospitalTreatmentRoom:
                return support_room_width, treatment_depth
            raise ValueError(f"Unhandled room semantic {semantic}")

        def add_vip_suite(
            suite_id: int,
            x0: float,
            x1: float,
            y0: float,
            y1: float,
            prefix: str,
            idx: int,
            corridor_door_y: float,
            window_y: float | None = None,
        ):
            total_width = x1 - x0
            lounge_width = float(np.clip(total_width * 0.38, 1.85, 2.35))
            lounge_width = min(lounge_width, total_width - 2.3)
            split_x = x0 + lounge_width

            lounge_name = room_name(Semantics.HospitalVIPLounge, 0, suite_id)
            treatment_name = room_name(Semantics.HospitalVIPTreatment, 0, suite_id)

            rooms[lounge_name] = {"shape": shapely.box(x0, y0, split_x, y1)}
            rooms[treatment_name] = {"shape": shapely.box(split_x, y0, x1, y1)}

            doors[f"door_{prefix}_{idx}_vip_lounge"] = {
                "shape": _horizontal_segment_biased(
                    x0,
                    split_x,
                    corridor_door_y,
                    interior_door_width,
                    side="start",
                ),
            }
            doors[f"door_{prefix}_{idx}_vip_internal"] = {
                "shape": _vertical_segment(
                    y0,
                    y1,
                    split_x,
                    interior_door_width,
                ),
            }

            if window_y is not None:
                add_room_windows(f"window_{prefix}_{idx}_vip_lounge", x0, split_x, window_y)
                add_room_windows(
                    f"window_{prefix}_{idx}_vip_treatment",
                    split_x,
                    x1,
                    window_y,
                )

        def add_room_sequence(
            room_types: list[Semantics],
            x_start: float,
            corridor_y0: float,
            corridor_y1: float,
            above: bool,
            prefix: str,
            width_overrides: dict[int, float] | None = None,
        ) -> float:
            nonlocal clinic_idx, vip_idx
            x_cursor = x_start
            for i, semantic in enumerate(room_types):
                width, depth = room_dims(semantic)
                if width_overrides is not None and i in width_overrides:
                    width = float(width_overrides[i])
                x0, x1 = x_cursor, x_cursor + width

                if semantic == Semantics.HospitalVIPClinic:
                    room_id = vip_idx
                    vip_idx += 1
                elif semantic == Semantics.HospitalClinic:
                    room_id = clinic_idx
                    clinic_idx += 1
                else:
                    room_id = 0

                name = room_name(semantic, 0, room_id)
                if above:
                    y0, y1 = corridor_y1, corridor_y1 + depth
                    door_y = corridor_y1
                    window_y = corridor_y1 + depth
                else:
                    y0, y1 = corridor_y0 - depth, corridor_y0
                    door_y = corridor_y0
                    window_y = corridor_y0 - depth

                if semantic == Semantics.HospitalVIPClinic:
                    add_vip_suite(
                        room_id,
                        x0,
                        x1,
                        y0,
                        y1,
                        prefix,
                        i,
                        door_y,
                        window_y,
                    )
                else:
                    rooms[name] = {"shape": shapely.box(x0, y0, x1, y1)}
                    doors[f"door_{prefix}_{i}"] = {
                        "shape": _horizontal_segment_biased(
                            x0,
                            x1,
                            door_y,
                            interior_door_width,
                            side="center",
                        ),
                    }
                    add_room_windows(f"window_{prefix}_{i}", x0, x1, window_y)
                x_cursor = x1
            return x_cursor

        def add_room_band_sequence(
            room_types: list[Semantics],
            x_start: float,
            band_y0: float,
            band_y1: float,
            prefix: str,
            *,
            door_to_upper: bool,
        ) -> float:
            nonlocal clinic_idx, vip_idx

            band_depth = band_y1 - band_y0
            x_cursor = x_start
            for i, semantic in enumerate(room_types):
                width, depth = room_dims(semantic)
                if depth > band_depth + 1e-6:
                    raise ValueError(
                        f"{semantic=} depth {depth} exceeds internal band depth {band_depth}"
                    )

                x0, x1 = x_cursor, x_cursor + width

                if semantic == Semantics.HospitalVIPClinic:
                    room_id = vip_idx
                    vip_idx += 1
                elif semantic == Semantics.HospitalClinic:
                    room_id = clinic_idx
                    clinic_idx += 1
                else:
                    room_id = 0

                if door_to_upper:
                    y1 = band_y1
                    y0 = band_y1 - depth
                    door_y = band_y1
                else:
                    y0 = band_y0
                    y1 = band_y0 + depth
                    door_y = band_y0

                name = room_name(semantic, 0, room_id)
                if semantic == Semantics.HospitalVIPClinic:
                    add_vip_suite(
                        room_id,
                        x0,
                        x1,
                        y0,
                        y1,
                        prefix,
                        i,
                        door_y,
                    )
                else:
                    rooms[name] = {"shape": shapely.box(x0, y0, x1, y1)}
                    doors[f"door_{prefix}_{i}"] = {
                        "shape": _horizontal_segment_biased(
                            x0,
                            x1,
                            door_y,
                            interior_door_width,
                            side="center",
                        ),
                    }
                x_cursor = x1
            return x_cursor

        def sequence_width(
            room_types: list[Semantics],
            width_overrides: dict[int, float] | None = None,
        ) -> float:
            total = 0.0
            for i, semantic in enumerate(room_types):
                width, _ = room_dims(semantic)
                if width_overrides is not None and i in width_overrides:
                    width = float(width_overrides[i])
                total += width
            return total

        def choose_width_override_target(
            room_types: list[Semantics],
        ) -> int | None:
            preferred_order = (
                Semantics.HospitalVIPClinic,
                Semantics.HospitalClinic,
                Semantics.HospitalExaminationRoom,
                Semantics.HospitalTreatmentRoom,
            )
            for semantic in preferred_order:
                for i in range(len(room_types) - 1, -1, -1):
                    if room_types[i] == semantic:
                        return i
            return None

        def build_clinic_sequence(
            standard_count: int,
            support_semantic: Semantics,
            vip_count: int,
            include_support_first: bool,
            prefix_standard_count: int = 0,
        ) -> list[Semantics]:
            prefix_standard_count = int(np.clip(prefix_standard_count, 0, standard_count))
            suffix_standard_count = standard_count - prefix_standard_count
            seq = [Semantics.HospitalClinic] * prefix_standard_count
            if include_support_first:
                seq.append(support_semantic)
            if vip_count > 0 and not vip_at_far_end:
                seq.extend([Semantics.HospitalVIPClinic] * vip_count)
            seq.extend([Semantics.HospitalClinic] * suffix_standard_count)
            if vip_count > 0 and vip_at_far_end:
                seq.extend([Semantics.HospitalVIPClinic] * vip_count)
            if not include_support_first:
                seq.append(support_semantic)
            return seq

        def build_rectangular_sequence(
            standard_count: int,
            support_semantic: Semantics,
            vip_count: int,
            prefix_standard_count: int = 0,
        ) -> list[Semantics]:
            prefix_standard_count = int(np.clip(prefix_standard_count, 0, standard_count))
            suffix_standard_count = standard_count - prefix_standard_count
            seq = [Semantics.HospitalClinic] * prefix_standard_count

            if vip_count > 0 and not vip_at_far_end:
                seq.extend([Semantics.HospitalVIPClinic] * vip_count)
                seq.append(support_semantic)
            else:
                seq.append(support_semantic)

            seq.extend([Semantics.HospitalClinic] * suffix_standard_count)

            if vip_count > 0 and vip_at_far_end:
                seq.extend([Semantics.HospitalVIPClinic] * vip_count)

            return seq

        if plan_form == "t_shape":
            reception_width_ratio = float(np.clip(reception_width_ratio, 0.2, 0.5))
            reception_width = lobby_width * reception_width_ratio
            waiting_width = lobby_width - reception_width
            if waiting_width <= 2.5:
                raise ValueError(
                    f"Front waiting width became too small: {waiting_width=}, check {lobby_width=} and {reception_width_ratio=}"
                )

            rooms[waiting_name] = {
                "shape": shapely.box(0, -waiting_depth, waiting_width, 0),
            }
            rooms[reception_name] = {
                "shape": shapely.box(waiting_width, -reception_depth, lobby_width, 0),
            }

            doors["door_waiting_corridor"] = {
                "shape": _horizontal_segment(0, waiting_width, 0, entrance_width),
            }
            doors["door_reception_corridor"] = {
                "shape": _horizontal_segment(
                    waiting_width, lobby_width, 0, interior_door_width
                ),
            }
            entrance["main_entrance"] = {
                "shape": _horizontal_segment(
                    0, waiting_width, -waiting_depth, entrance_width
                ),
            }

            add_room_windows_vertical("window_waiting", -waiting_depth, 0, 0)
            add_room_windows_vertical(
                "window_reception",
                -reception_depth,
                0,
                lobby_width,
            )

            clinic_start_x = lobby_width + front_buffer_length
            top_front_standard = shared_front_standard
            bottom_front_standard = shared_front_standard
            top_wing_standard = top_standard_total - top_front_standard
            bottom_wing_standard = bottom_standard_total - bottom_front_standard

            main_top_end = add_room_sequence(
                [Semantics.HospitalClinic] * top_front_standard,
                clinic_start_x,
                0,
                corridor_width,
                above=True,
                prefix="main_top",
            )
            main_bottom_end = add_room_sequence(
                [Semantics.HospitalClinic] * bottom_front_standard,
                clinic_start_x,
                0,
                corridor_width,
                above=False,
                prefix="main_bottom",
            )

            branch_x = max(clinic_start_x, main_top_end, main_bottom_end)
            upper_corridor_y0 = corridor_width
            upper_corridor_y1 = corridor_width * 2
            lower_corridor_y0 = -corridor_width
            lower_corridor_y1 = 0

            upper_wing_types = build_clinic_sequence(
                top_wing_standard,
                Semantics.HospitalExaminationRoom,
                vip_count=top_vip_total,
                include_support_first=True,
            )
            lower_wing_types = build_clinic_sequence(
                bottom_wing_standard,
                Semantics.HospitalTreatmentRoom,
                vip_count=bottom_vip_total,
                include_support_first=True,
            )

            upper_end = add_room_sequence(
                upper_wing_types,
                branch_x,
                upper_corridor_y0,
                upper_corridor_y1,
                above=True,
                prefix="upper_wing",
            )
            lower_end = add_room_sequence(
                lower_wing_types,
                branch_x,
                lower_corridor_y0,
                lower_corridor_y1,
                above=False,
                prefix="lower_wing",
            )

            corridor_end = max(branch_x + corridor_connector_length, lobby_width)
            corridor_shape = shapely.union_all(
                [
                    shapely.box(0, 0, corridor_end, corridor_width),
                    shapely.box(branch_x, upper_corridor_y0, upper_end, upper_corridor_y1),
                    shapely.box(branch_x, lower_corridor_y0, lower_end, lower_corridor_y1),
                ]
            )
        else:
            # In the default rectangular dental layout we want three visually
            # readable clusters along the corridor:
            #   support core -> standard operatory cluster -> VIP cluster.
            # So we keep the support pair at the front of the clinical band
            # instead of splitting standard clinics before/after it.
            public_block_width = lobby_width
            dual_corridor_threshold = int(
                max(
                    1,
                    multi_corridor_threshold
                    if multi_corridor_threshold is not None
                    else dual_corridor_threshold,
                )
            )
            triple_corridor_threshold = int(
                max(
                    dual_corridor_threshold + 1,
                    four_row_threshold
                    if four_row_threshold is not None
                    else triple_corridor_threshold,
                )
            )
            use_four_row = num_clinics >= triple_corridor_threshold
            use_multi_corridor = num_clinics >= min(
                dual_corridor_threshold, triple_corridor_threshold
            )

            reception_width_ratio = float(np.clip(reception_width_ratio, 0.18, 0.42))
            reception_width = public_block_width * reception_width_ratio
            waiting_width = public_block_width - reception_width
            if waiting_width <= 3.0:
                raise ValueError(
                    f"Waiting width became too small: {waiting_width=}, check {lobby_width=} and {reception_width_ratio=}"
                )
            reception_x0 = waiting_width

            if use_multi_corridor:
                def build_linear_cluster(
                    standard_count: int,
                    vip_count: int = 0,
                ) -> list[Semantics]:
                    seq = []
                    if vip_count > 0 and not vip_at_far_end:
                        seq.extend([Semantics.HospitalVIPClinic] * vip_count)
                    seq.extend([Semantics.HospitalClinic] * standard_count)
                    if vip_count > 0 and vip_at_far_end:
                        seq.extend([Semantics.HospitalVIPClinic] * vip_count)
                    return seq

                if use_four_row:
                    if vip_cluster_side == "top":
                        row_vips = [num_vip, 0, 0, 0]
                    elif vip_cluster_side == "bottom":
                        row_vips = [0, 0, 0, num_vip]
                    else:
                        split_top_vips, split_bottom_vips = _split_even(num_vip)
                        row_vips = [split_top_vips, 0, 0, split_bottom_vips]

                    standard_row_counts = _allocate_standard_counts(
                        num_standard,
                        [
                            row_vips[0] * vip_clinic_width,
                            support_room_width,
                            support_room_width,
                            row_vips[3] * vip_clinic_width,
                        ],
                        standard_clinic_width,
                    )

                    top_outer_types = build_linear_cluster(
                        standard_row_counts[0],
                        row_vips[0],
                    )
                    upper_inner_types = [Semantics.HospitalExaminationRoom]
                    upper_inner_types.extend(
                        [Semantics.HospitalClinic] * standard_row_counts[1]
                    )
                    lower_inner_types = [Semantics.HospitalTreatmentRoom]
                    lower_inner_types.extend(
                        build_linear_cluster(
                            standard_row_counts[2],
                            row_vips[2],
                        )
                    )
                    bottom_outer_types = build_linear_cluster(
                        standard_row_counts[3],
                        row_vips[3],
                    )

                    top_depth = max(
                        standard_clinic_depth if standard_row_counts[0] > 0 else 0.0,
                        vip_clinic_depth if row_vips[0] > 0 else 0.0,
                    )
                    upper_inner_depth = max(
                        examination_depth,
                        treatment_depth,
                        standard_clinic_depth if standard_row_counts[1] > 0 else 0.0,
                    )
                    lower_inner_depth = max(
                        treatment_depth,
                        standard_clinic_depth if standard_row_counts[2] > 0 else 0.0,
                        vip_clinic_depth if row_vips[2] > 0 else 0.0,
                    )
                    bottom_depth = max(
                        standard_clinic_depth if standard_row_counts[3] > 0 else 0.0,
                        vip_clinic_depth if row_vips[3] > 0 else 0.0,
                    )

                    lower_corridor_y0 = 0.0
                    lower_corridor_y1 = corridor_width
                    lower_inner_y0 = lower_corridor_y1
                    lower_inner_y1 = lower_inner_y0 + lower_inner_depth
                    middle_corridor_y0 = lower_inner_y1
                    middle_corridor_y1 = middle_corridor_y0 + corridor_width
                    upper_inner_y0 = middle_corridor_y1
                    upper_inner_y1 = upper_inner_y0 + upper_inner_depth
                    upper_corridor_y0 = upper_inner_y1
                    upper_corridor_y1 = upper_corridor_y0 + corridor_width

                    public_y0 = -bottom_depth
                    public_y1 = upper_corridor_y1 + top_depth

                    rooms[waiting_name] = {
                        "shape": shapely.box(0, public_y0, waiting_width, 0.0),
                    }
                    rooms[reception_name] = {
                        "shape": shapely.box(
                            reception_x0, public_y0, public_block_width, 0.0
                        ),
                    }

                    entrance["main_entrance"] = {
                        "shape": _horizontal_segment(
                            0, waiting_width, public_y0, entrance_width
                        ),
                    }
                    opens["open_public_zone"] = {
                        "shape": _vertical_segment(
                            public_y0,
                            0.0,
                            waiting_width,
                            public_zone_open_width,
                        ),
                    }
                    doors["door_waiting_to_hall"] = {
                        "shape": _horizontal_segment(
                            0,
                            waiting_width,
                            0.0,
                            entrance_width,
                        ),
                    }
                    doors["door_reception_to_hall"] = {
                        "shape": _horizontal_segment(
                            reception_x0,
                            public_block_width,
                            0.0,
                            interior_door_width,
                        ),
                    }
                    add_room_windows_vertical("window_waiting", public_y0, 0.0, 0)
                    add_room_windows(
                        "window_reception",
                        reception_x0,
                        public_block_width,
                        public_y0,
                    )

                    connector_x0 = public_block_width
                    connector_x1 = public_block_width + corridor_connector_length
                    clinic_start_x = connector_x1 + front_buffer_length

                    top_outer_end = add_room_sequence(
                        top_outer_types,
                        clinic_start_x,
                        upper_corridor_y0,
                        upper_corridor_y1,
                        above=True,
                        prefix="rect_top_outer",
                    )
                    bottom_outer_end = add_room_sequence(
                        bottom_outer_types,
                        clinic_start_x,
                        lower_corridor_y0,
                        lower_corridor_y1,
                        above=False,
                        prefix="rect_bottom_outer",
                    )
                    lower_inner_end = add_room_band_sequence(
                        lower_inner_types,
                        clinic_start_x,
                        lower_inner_y0,
                        lower_inner_y1,
                        prefix="rect_lower_inner",
                        door_to_upper=True,
                    )
                    upper_inner_end = add_room_band_sequence(
                        upper_inner_types,
                        clinic_start_x,
                        upper_inner_y0,
                        upper_inner_y1,
                        prefix="rect_upper_inner",
                        door_to_upper=False,
                    )

                    corridor_shape = shapely.union_all(
                        [
                            shapely.box(0, 0.0, public_block_width, public_y1),
                            shapely.box(
                                connector_x0,
                                lower_corridor_y0,
                                connector_x1,
                                upper_corridor_y1,
                            ),
                            shapely.box(
                                connector_x0,
                                lower_corridor_y0,
                                max(connector_x1, bottom_outer_end),
                                lower_corridor_y1,
                            ),
                            shapely.box(
                                connector_x0,
                                middle_corridor_y0,
                                max(connector_x1, lower_inner_end, upper_inner_end),
                                middle_corridor_y1,
                            ),
                            shapely.box(
                                connector_x0,
                                upper_corridor_y0,
                                max(connector_x1, top_outer_end),
                                upper_corridor_y1,
                            ),
                        ]
                    )
                else:
                    if vip_cluster_side == "top":
                        top_vip_multi, bottom_vip_multi, middle_vip_multi = num_vip, 0, 0
                    elif vip_cluster_side == "bottom":
                        top_vip_multi, bottom_vip_multi, middle_vip_multi = 0, num_vip, 0
                    else:
                        top_vip_multi, bottom_vip_multi = _split_even(num_vip)
                        middle_vip_multi = 0

                    top_standard_multi, middle_standard_multi, bottom_standard_multi = (
                        _allocate_standard_counts(
                            num_standard,
                            [
                                top_vip_multi * vip_clinic_width,
                                2 * support_room_width
                                + middle_vip_multi * vip_clinic_width,
                                bottom_vip_multi * vip_clinic_width,
                            ],
                            standard_clinic_width,
                        )
                    )

                    upper_types = build_linear_cluster(
                        top_standard_multi,
                        top_vip_multi,
                    )
                    lower_types = build_linear_cluster(
                        bottom_standard_multi,
                        bottom_vip_multi,
                    )

                    middle_types = [
                        Semantics.HospitalExaminationRoom,
                        Semantics.HospitalTreatmentRoom,
                    ]
                    middle_types.extend(
                        [Semantics.HospitalClinic] * middle_standard_multi
                    )
                    if middle_vip_multi > 0:
                        vip_band = [Semantics.HospitalVIPClinic] * middle_vip_multi
                        if vip_at_far_end:
                            middle_types.extend(vip_band)
                        else:
                            middle_types = vip_band + middle_types

                    top_depth = max(
                        standard_clinic_depth if top_standard_multi > 0 else 0.0,
                        vip_clinic_depth if top_vip_multi > 0 else 0.0,
                    )
                    bottom_depth = max(
                        standard_clinic_depth if bottom_standard_multi > 0 else 0.0,
                        vip_clinic_depth if bottom_vip_multi > 0 else 0.0,
                    )
                    middle_band_depth = max(
                        examination_depth,
                        treatment_depth,
                        standard_clinic_depth if middle_standard_multi > 0 else 0.0,
                        vip_clinic_depth if middle_vip_multi > 0 else 0.0,
                    )

                    lower_corridor_y0 = 0.0
                    lower_corridor_y1 = corridor_width
                    middle_band_y0 = lower_corridor_y1
                    middle_band_y1 = middle_band_y0 + middle_band_depth
                    upper_corridor_y0 = middle_band_y1
                    upper_corridor_y1 = upper_corridor_y0 + corridor_width

                    public_y0 = -bottom_depth
                    public_y1 = upper_corridor_y1 + top_depth

                    rooms[waiting_name] = {
                        "shape": shapely.box(0, public_y0, waiting_width, 0.0),
                    }
                    rooms[reception_name] = {
                        "shape": shapely.box(
                            reception_x0, public_y0, public_block_width, 0.0
                        ),
                    }

                    entrance["main_entrance"] = {
                        "shape": _horizontal_segment(
                            0, waiting_width, public_y0, entrance_width
                        ),
                    }
                    opens["open_public_zone"] = {
                        "shape": _vertical_segment(
                            public_y0,
                            0.0,
                            waiting_width,
                            public_zone_open_width,
                        ),
                    }
                    doors["door_waiting_to_hall"] = {
                        "shape": _horizontal_segment(
                            0,
                            waiting_width,
                            0.0,
                            entrance_width,
                        ),
                    }
                    doors["door_reception_to_hall"] = {
                        "shape": _horizontal_segment(
                            reception_x0,
                            public_block_width,
                            0.0,
                            interior_door_width,
                        ),
                    }
                    add_room_windows_vertical("window_waiting", public_y0, 0.0, 0)
                    add_room_windows(
                        "window_reception",
                        reception_x0,
                        public_block_width,
                        public_y0,
                    )

                    connector_x0 = public_block_width
                    connector_x1 = public_block_width + corridor_connector_length
                    clinic_start_x = connector_x1 + front_buffer_length

                    upper_end = add_room_sequence(
                        upper_types,
                        clinic_start_x,
                        upper_corridor_y0,
                        upper_corridor_y1,
                        above=True,
                        prefix="rect_top",
                    )
                    lower_end = add_room_sequence(
                        lower_types,
                        clinic_start_x,
                        lower_corridor_y0,
                        lower_corridor_y1,
                        above=False,
                        prefix="rect_bottom",
                    )

                    middle_attach_to_upper = sequence_width(upper_types) <= sequence_width(
                        lower_types
                    )
                    middle_end = add_room_band_sequence(
                        middle_types,
                        clinic_start_x,
                        middle_band_y0,
                        middle_band_y1,
                        prefix="rect_middle",
                        door_to_upper=middle_attach_to_upper,
                    )

                    upper_corridor_end = max(
                        connector_x1,
                        upper_end,
                        middle_end if middle_attach_to_upper else connector_x1,
                    )
                    lower_corridor_end = max(
                        connector_x1,
                        lower_end,
                        middle_end if not middle_attach_to_upper else connector_x1,
                    )

                    corridor_shape = shapely.union_all(
                        [
                            shapely.box(0, 0.0, public_block_width, public_y1),
                            shapely.box(
                                connector_x0,
                                lower_corridor_y0,
                                connector_x1,
                                upper_corridor_y1,
                            ),
                            shapely.box(
                                connector_x0,
                                lower_corridor_y0,
                                lower_corridor_end,
                                lower_corridor_y1,
                            ),
                            shapely.box(
                                connector_x0,
                                upper_corridor_y0,
                                upper_corridor_end,
                                upper_corridor_y1,
                            ),
                        ]
                    )
            else:
                prefix_standard_count = 0
                public_block_width = min(
                    public_block_width,
                    max(
                        6.4,
                        support_room_width + 1.2,
                        standard_clinic_width + 2.4,
                    ),
                )
                clinic_start_x = public_block_width + front_buffer_length
                upper_types = build_rectangular_sequence(
                    top_standard_total,
                    Semantics.HospitalExaminationRoom,
                    vip_count=top_vip_total,
                    prefix_standard_count=prefix_standard_count,
                )
                lower_types = build_rectangular_sequence(
                    bottom_standard_total,
                    Semantics.HospitalTreatmentRoom,
                    vip_count=bottom_vip_total,
                    prefix_standard_count=prefix_standard_count,
                )

                top_depth = max(
                    examination_depth,
                    standard_clinic_depth,
                    vip_clinic_depth if top_vip_total > 0 else 0.0,
                )
                bottom_depth = max(
                    treatment_depth,
                    standard_clinic_depth,
                    vip_clinic_depth if bottom_vip_total > 0 else 0.0,
                )
                public_y0 = -bottom_depth
                public_y1 = corridor_width + top_depth
                waiting_y0 = -min(waiting_depth, bottom_depth)
                waiting_y1 = 0.0
                reception_y0 = 0.0
                reception_y1 = float(max(corridor_width, 1.0))
                corridor_front_y0 = reception_y1
                corridor_front_y1 = corridor_width

                rooms[waiting_name] = {
                    "shape": shapely.box(0, waiting_y0, public_block_width, waiting_y1),
                }
                rooms[reception_name] = {
                    "shape": shapely.box(
                        0, reception_y0, public_block_width, reception_y1
                    ),
                }

                entrance["main_entrance"] = {
                    "shape": _horizontal_segment(
                        0, public_block_width, waiting_y0, entrance_width
                    ),
                }
                opens["open_public_zone"] = {
                    "shape": _horizontal_segment(
                        0, public_block_width, waiting_y1, public_zone_open_width
                    ),
                }
                doors["door_public_to_corridor_main"] = {
                    "shape": _vertical_segment(
                        reception_y0,
                        min(reception_y1, corridor_width),
                        public_block_width,
                        entrance_width,
                    ),
                }
                add_room_windows_vertical(
                    "window_waiting", waiting_y0, waiting_y1, 0
                )
                add_room_windows_vertical(
                    "window_reception", reception_y0, reception_y1, 0
                )

                upper_width = sequence_width(upper_types)
                lower_width = sequence_width(lower_types)
                upper_width_overrides = None
                lower_width_overrides = None
                if upper_width < lower_width and upper_types:
                    target_idx = choose_width_override_target(upper_types)
                    if target_idx is not None:
                        upper_width_overrides = {
                            target_idx: room_dims(upper_types[target_idx])[0]
                            + (lower_width - upper_width)
                        }
                elif lower_width < upper_width and lower_types:
                    target_idx = choose_width_override_target(lower_types)
                    if target_idx is not None:
                        lower_width_overrides = {
                            target_idx: room_dims(lower_types[target_idx])[0]
                            + (upper_width - lower_width)
                        }

                upper_end = add_room_sequence(
                    upper_types,
                    clinic_start_x,
                    0,
                    corridor_width,
                    above=True,
                    prefix="rect_top",
                    width_overrides=upper_width_overrides,
                )
                lower_end = add_room_sequence(
                    lower_types,
                    clinic_start_x,
                    0,
                    corridor_width,
                    above=False,
                    prefix="rect_bottom",
                    width_overrides=lower_width_overrides,
                )

                corridor_geoms = [
                    shapely.box(
                        public_block_width,
                        0,
                        max(
                            upper_end,
                            lower_end,
                            clinic_start_x + corridor_connector_length,
                        ),
                        corridor_width,
                    )
                ]
                if corridor_front_y1 - corridor_front_y0 > 1e-6:
                    corridor_geoms.append(
                        shapely.box(
                            0,
                            corridor_front_y0,
                            public_block_width,
                            corridor_front_y1,
                        )
                    )

                corridor_shape = shapely.union_all(corridor_geoms)

        rooms[corridor_name] = {
            "shape": corridor_shape,
        }

        return {
            "rooms": rooms,
            "doors": doors,
            "windows": windows,
            "entrance": entrance,
            "opens": opens,
        }
