! rule: S7.4.4.2-005
! covers: runtime-negative
! evidence: effect
! standard: f2023
program character_type_case
    implicit none
    call check(-2)
    call check(0)
    call check(3)
contains
    subroutine check(n)
        integer, intent(in) :: n
        character(len=n) :: text
        text = 'ABC'
        if (len(text) /= max(n,0)) error stop 1
        if (n == 3) then
            if (text /= 'ABC') error stop 2
        end if
    end subroutine
end program
