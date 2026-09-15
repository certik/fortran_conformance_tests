! rule: S7.4.4.2-006
! covers: ordinary-dummy-length
! evidence: effect
! standard: f2023
program character_type_case
    implicit none
    call check('', 0)
    call check('AB', 2)
    call check('ABCDE', 5)
    call prefix('ABCDE')
contains
    subroutine check(text, expected)
        character(*), intent(in) :: text
        integer, intent(in) :: expected
        if (len(text) /= expected) error stop 1
        if (expected > 0) then
            if (text(1:1) /= 'A') error stop 2
        end if
        if (expected == 5) then
            if (text(5:5) /= 'E') error stop 3
        end if
    end subroutine
    subroutine prefix(text)
        character(3), intent(in) :: text
        if (len(text) /= 3 .or. text /= 'ABC') error stop 4
    end subroutine
end program
