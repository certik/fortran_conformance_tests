! rule: S10.2.1.3-018
! covers: true false same-kind different-kind logical-array
! profile: two-logical-kinds
! F2023 10.2.1.3 p10. No assertion about the integer representation of logicals.
program s10_2_1_3_018_valid
    use iso_fortran_env, only: logical_kinds
    implicit none
    integer, parameter :: other = maxval(logical_kinds, mask=logical_kinds /= kind(.true.))
    logical :: normal, normal_array(3)
    logical(other) :: different, different_array(3)
    normal = .true.
    different = normal
    if (.not. different) error stop 'true-to-other'
    normal = .false.
    different = normal
    if (different) error stop 'false-to-other'
    different = .true._other
    normal = different
    if (.not. normal) error stop 'true-to-default'
    different = .false._other
    normal = different
    if (normal) error stop 'false-to-default'
    normal_array = [.true., .false., .true.]
    different_array = normal_array
    if (any(different_array .neqv. [.true._other, .false._other, .true._other])) error stop 'array-to-other'
    normal_array = .false.
    normal_array = different_array
    if (any(normal_array .neqv. [.true., .false., .true.])) error stop 'array-to-default'
    normal = normal_array(1)
    if (.not. normal) error stop 'same-kind'
end program
