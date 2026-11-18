#pragma once

namespace path_execution {
// A certified prefix may finish before the next local plan arrives. Only the
// same live dispatch can bridge that gap, and its output stays at zero.
inline constexpr double kSegmentRolloverSeconds = .65;
inline bool segmentRolloverValid(double until, double now, double lease_age,
                                  bool same_route, bool stopping) {
    return until > now && lease_age >= 0. && lease_age <= 1.5
        && same_route && !stopping;
}
}
