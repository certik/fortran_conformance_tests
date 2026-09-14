! rule: R704
! covers: character-default character-selector
! evidence: positive-control
program p
    implicit none
    character :: a = 'a'
    character(len=3, kind=kind('a')) :: b = 'bcd'
    if (a /= 'a') error stop 1
    if (b /= 'bcd') error stop 2
end program
