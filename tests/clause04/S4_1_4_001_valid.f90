! rule: S4.1.4-001
! covers: newline-control semicolon-control standalone-label-control embedded-if-control embedded-where-control
! evidence: positive-control
program statement_contexts
    implicit none
    integer :: value
    integer :: values(1)
    logical :: mask(1)
    value = 0
    value = 1; value = value + 1
10  if (value == 2) value = 3
    mask = .true.
    values = 0
    where (mask) values = 4
    if (value /= 3) stop 1
    if (values(1) /= 4) stop 2
end program statement_contexts
