! rule: S7.4.4.2-001
! covers: bare-default-kind
! evidence: effect
! standard: f2023
program character_type_case
    implicit none
    character :: text
    text = 'A'
    if (kind(text) /= kind('A') .or. len(text) /= 1) error stop 1
    call check(text)
contains
    subroutine check(value)
        character, intent(in) :: value
        if (value /= 'A') error stop 2
    end subroutine
end program
