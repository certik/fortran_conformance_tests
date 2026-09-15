! rule: S7.4.4.2-006
! covers: guard-selector-length
! evidence: effect
! standard: f2023
program character_type_case
    implicit none
    call check('', 0)
    call check('AB', 2)
    call check('ABCDE', 5)
contains
    subroutine check(value, expected)
        class(*), intent(in) :: value
        integer, intent(in) :: expected
        select type (text => value)
        type is (character(len=*,kind=kind('A')))
            if (len(text) /= expected .or. kind(text) /= kind('A')) error stop 1
            if (expected > 0) then
                if (text(1:1) /= 'A') error stop 2
            end if
            if (expected == 5) then
                if (text /= 'ABCDE') error stop 3
            end if
        class default
            error stop 4
        end select
    end subroutine
end program
