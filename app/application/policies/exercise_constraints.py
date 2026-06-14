from app.domain.enums import Constraint, MovementPattern

PATTERN_EXCLUSIONS: dict[Constraint, set[MovementPattern]] = {
    Constraint.NO_OVERHEAD: {MovementPattern.PUSH_VERTICAL},
    Constraint.NO_SHOULDER_LOAD: {MovementPattern.PUSH_VERTICAL, MovementPattern.PUSH_HORIZONTAL},
    Constraint.NO_KNEE_LOAD: {MovementPattern.SQUAT, MovementPattern.LUNGE},
    Constraint.NO_HINGE: {MovementPattern.HINGE},
    Constraint.NO_HORIZONTAL_PRESS: {MovementPattern.PUSH_HORIZONTAL},
    Constraint.NO_CARRY: {MovementPattern.CARRY},
}

EQUIPMENT_EXCLUSIONS: dict[Constraint, set[str]] = {
    Constraint.NO_BARBELL: {"barbell"},
}