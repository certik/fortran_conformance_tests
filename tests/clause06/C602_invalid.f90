! rule: C602
! covers: noninteger-literal
! Each case becomes conforming when its repeat operand is replaced by 2.
! case: real-literal
program real_literal_repeat
    implicit none
    integer :: values(2)
    data values /2.0 * 7/ ! {error C602 real-literal}
end program real_literal_repeat
! case: complex-literal
program complex_literal_repeat
    implicit none
    integer :: values(2)
    data values /(2, 0) * 7/ ! {error C602 complex-literal}
end program complex_literal_repeat
! case: logical-literal
program logical_literal_repeat
    implicit none
    integer :: values(2)
    data values /.true. * 7/ ! {error C602 logical-literal}
end program logical_literal_repeat
! case: character-literal
program character_literal_repeat
    implicit none
    integer :: values(2)
    data values /'2' * 7/ ! {error C602 character-literal}
end program character_literal_repeat
