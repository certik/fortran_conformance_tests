! rule: S7.4.5-004
! covers: unsuffixed-true unsuffixed-false
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    logical :: a = .true.
    if (kind(.true.) /= kind(.false.)) error stop 1
    if (kind(.false.) /= kind(a)) error stop 2
    if (.not. .true.) error stop 3
    if (.false.) error stop 4
end program numeric_literal_case
