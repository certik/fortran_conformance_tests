! rule: S7.1.2-002
! covers: local-intrinsic-keywords
! evidence: effect
program type_basics_intrinsic_local
    implicit none
    integer :: i = 7
    real :: r = 0.0
    complex :: z = (0.0, 0.0)
    character :: c = 'A'
    logical :: l = .true.

    if (i /= 7) error stop 1
    if (r /= 0.0) error stop 2
    if (z /= (0.0, 0.0)) error stop 3
    if (c /= 'A') error stop 4
    if (.not. l) error stop 5
end program type_basics_intrinsic_local
