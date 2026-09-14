! rule: C602
! covers: noninteger-named
! Every repeat name is a previously defined scalar PARAMETER.
! One object and one intended repetition avoid an incidental count-mismatch rejection.
! case: real-named
program real_named_repeat
    implicit none
    real, parameter :: repeats = 1
    integer :: values(1)
    data values /repeats * 7/ ! {error C602 real-named}
end program real_named_repeat
! case: complex-named
program complex_named_repeat
    implicit none
    complex, parameter :: repeats = 1
    integer :: values(1)
    data values /repeats * 7/ ! {error C602 complex-named}
end program complex_named_repeat
! case: logical-named
program logical_named_repeat
    implicit none
    logical, parameter :: repeats = .true.
    integer :: values(1)
    data values /repeats * 7/ ! {error C602 logical-named}
end program logical_named_repeat
! case: character-named
program character_named_repeat
    implicit none
    character(len=1), parameter :: repeats = '1'
    integer :: values(1)
    data values /repeats * 7/ ! {error C602 character-named}
end program character_named_repeat
