! rule: S7.4.1-001
! covers: integer-parameter
! evidence: effect
program p
    implicit none
    integer :: value = 0
    if (kind(value%kind) /= kind(0)) error stop 1
    call check(value%kind, kind(0))
contains
    subroutine check(parameter, expected)
        integer, intent(in) :: parameter, expected
        if (parameter /= expected) error stop 2
    end subroutine
end program
