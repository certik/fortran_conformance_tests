! rule: S7.1.2-002
! covers: private-module-intrinsic-keywords
! evidence: effect
module type_basics_private_intrinsics
    implicit none
    private
    public :: check_values
    integer :: i = 11
    real :: r = 0.0
    complex :: z = (0.0, 0.0)
    character :: c = 'B'
    logical :: l = .false.
contains
    subroutine check_values()
        if (i /= 11) error stop 1
        if (r /= 0.0) error stop 2
        if (z /= (0.0, 0.0)) error stop 3
        if (c /= 'B') error stop 4
        if (l) error stop 5
    end subroutine check_values
end module type_basics_private_intrinsics

program type_basics_private
    use type_basics_private_intrinsics, only: check_values
    implicit none
    call check_values()
end program type_basics_private
