! rule: S7.2-002
! covers: intrinsic-kind-integer-names
! evidence: effect
program type_parameters_intrinsic_names
    implicit none
    integer :: i = 0
    real :: r = 0.0
    complex :: z = (0.0, 0.0)
    logical :: l = .false.
    character(len=2) :: c = 'AB'

    call check_parameter(i%kind, kind(i))
    call check_parameter(r%kind, kind(r))
    call check_parameter(z%kind, kind(z))
    call check_parameter(l%kind, kind(l))
    call check_parameter(c%kind, kind(c))
contains
    subroutine check_parameter(value, expected)
        integer, intent(in) :: value, expected
        if (value /= expected) error stop 1
    end subroutine check_parameter
end program type_parameters_intrinsic_names
