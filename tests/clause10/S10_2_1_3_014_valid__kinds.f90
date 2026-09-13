! rule: S10.2.1.3-014
! covers: integer-kind-change
! profile: two-integer-kinds
! F2023 10.2.1.3 p8, Table 10.9.
program s10_2_1_3_014_kinds
    use iso_fortran_env, only: integer_kinds
    implicit none
    integer, parameter :: other = maxval(integer_kinds, mask=integer_kinds /= kind(0))
    integer :: normal, normal_array(3)
    integer(other) :: different, different_array(3)
    normal = -17
    different = normal
    if (different /= -17_other) error stop 'default-to-other'
    different = 29_other
    normal = different
    if (normal /= 29) error stop 'other-to-default'
    normal_array = [2, -5, 9]
    different_array = normal_array
    if (any(different_array /= [2_other, -5_other, 9_other])) error stop 'array-to-other'
    normal_array = different_array
    if (any(normal_array /= [2, -5, 9])) error stop 'array-to-default'
end program
