! rule: S7.4.1-001
! covers: character-parameter
! evidence: effect
program p
    implicit none
    character(len=3, kind=kind('a')) :: value = 'abc'
    if (kind(value%kind) /= kind(0)) error stop 1
    call check(value%kind, kind('a'))
contains
    subroutine check(parameter, expected)
        integer, intent(in) :: parameter, expected
        if (parameter /= expected) error stop 2
    end subroutine
end program
