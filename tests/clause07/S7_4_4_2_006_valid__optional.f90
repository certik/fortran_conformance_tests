! rule: S7.4.4.2-006
! covers: optional-dummy-presence
! evidence: effect
! standard: f2023
program character_type_case
    implicit none
    integer :: observed
    call check(observed)
    if (observed /= -1) error stop 1
    call check(observed, '')
    if (observed /= 0) error stop 2
    call check(observed, 'ABC')
    if (observed /= 3) error stop 3
contains
    subroutine check(observed, text)
        integer, intent(out) :: observed
        character(*), optional, intent(in) :: text
        if (present(text)) then
            observed = len(text)
            if (len(text) == 3) then
                if (text /= 'ABC') error stop 4
            end if
        else
            observed = -1
        end if
    end subroutine
end program
