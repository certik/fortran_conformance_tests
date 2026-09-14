! rule: S7.4.1-001
! covers: logical-parameter
! evidence: effect
program p
    implicit none
    logical :: value = .true.
    if (kind(value%kind) /= kind(0)) error stop 1
    call check(value%kind, kind(.true.))
contains
    subroutine check(parameter, expected)
        integer, intent(in) :: parameter, expected
        if (parameter /= expected) error stop 2
    end subroutine
end program
