! rule: S7.4.4.3-001
! covers: omitted-prefix-default
! evidence: effect
! standard: f2023
program character_type_case
    implicit none
    if (kind('') /= kind('A') .or. kind("") /= kind('A')) error stop 1
    if (kind('ABC') /= kind('A') .or. kind("xyz") /= kind('A')) error stop 2
    if (len('') /= 0 .or. len("") /= 0) error stop 3
    if (len('ABC') /= 3 .or. len("xyz") /= 3) error stop 4
    call check('ABC')
    call check("ABC")
contains
    subroutine check(value)
        character(*), intent(in) :: value
        if (len(value) /= 3 .or. value /= 'ABC') error stop 5
    end subroutine
end program
