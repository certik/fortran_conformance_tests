! rule: S7.4.1-001
! covers: complex-parameter
! evidence: effect
program p
    implicit none
    complex(kind=kind(0.0d0)) :: value = (0.0d0, 0.0d0)
    if (kind(value%kind) /= kind(0)) error stop 1
    call check(value%kind, kind(0.0d0))
contains
    subroutine check(parameter, expected)
        integer, intent(in) :: parameter, expected
        if (parameter /= expected) error stop 2
    end subroutine
end program
