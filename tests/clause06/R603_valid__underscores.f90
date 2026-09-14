! rule: R603
! covers: embedded-underscore consecutive-underscores trailing-underscore
! evidence: positive-control
! Free-form source; underscore count and position must not merge these names.
program names_underscores
    implicit none
    integer :: a_b, a__b, a_b_, a_, b__, c1__2_d_

    a_b = 11
    a__b = 17
    a_b_ = 23
    a_ = 31
    b__ = 37
    c1__2_d_ = 41

    if (a_b /= 11) error stop 1
    if (a__b /= 17) error stop 2
    if (a_b_ /= 23) error stop 3
    if (a_ /= 31) error stop 4
    if (b__ /= 37) error stop 5
    if (c1__2_d_ /= 41) error stop 6
end program names_underscores
