! rule: S7.4.5-001
! covers: default-truth-values
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    logical :: t = .true., f = .false.
    if (.not. t) error stop 1
    if (f) error stop 2
    if (t .eqv. f) error stop 3
    if (.not. (t .neqv. f)) error stop 4
    if (.not. (t .eqv. .not. f)) error stop 5
end program numeric_literal_case
