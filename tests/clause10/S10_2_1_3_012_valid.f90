! rule: S10.2.1.3-012
! covers: rank-one higher-rank array-section empty-destination scalar-from-destination
! F2023 10.2.1.3 p5.
program s10_2_1_3_012_valid
    implicit none
    integer :: a(6), b(2, 3), empty(0)
    a = 7
    if (any(a /= 7)) error stop 'rank-one'
    b = -3
    if (any(b /= -3)) error stop 'higher-rank'
    a = [2, 5, 9, 14, 20, 27]
    a(2:6:2) = 41
    if (any(a /= [2, 41, 9, 41, 20, 41])) error stop 'array-section'
    a = a(2)
    if (any(a /= 41)) error stop 'scalar-from-destination'
    empty = 17
    if (size(empty) /= 0) error stop 'empty-destination'
end program
