! rule: R709
! covers: digit-string zero-padded-kind-digits
! evidence: positive-control
! profile: integer-literal-kind-eight
program p
    implicit none
    integer, parameter :: selector = 8
    integer(selector) :: a, b
    data a, b /43_8, 47_0008/
    if (a /= 40_selector + 3_selector) error stop 1
    if (b /= 40_selector + 7_selector) error stop 2
end program
