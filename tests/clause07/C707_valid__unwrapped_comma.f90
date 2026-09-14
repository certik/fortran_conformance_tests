! rule: C707
! covers: unwrapped-comma
! evidence: positive-control
program c707_unwrapped_comma
    implicit none
    character*3, plain
    plain = 'def'
    if (len(plain) /= 3) error stop 'length'
    if (plain /= 'def') error stop 'value'
end program
