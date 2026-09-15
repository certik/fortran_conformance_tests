! rule: R722
! covers: parenthesized-lengths
! evidence: positive-control
! standard: f2023
program character_type_case
    implicit none
    character(3) :: positional
    character(len=3) :: keyword
    positional = 'ABC'
    keyword = 'xyz'
    if (len(positional) /= 3 .or. len(keyword) /= 3) error stop 1
    if (positional /= 'ABC' .or. keyword /= 'xyz') error stop 2
    call automatic(3)
contains
    subroutine automatic(n)
        integer, intent(in) :: n
        character(len=n) :: text
        text = 'DEF'
        if (len(text) /= n) error stop 3
        if (text /= 'DEF') error stop 4
    end subroutine
end program
