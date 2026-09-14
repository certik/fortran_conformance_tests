! rule: S6.2.5-007
! covers: output-format input-format distinct-formats
program label_formats
    implicit none
    character(4) :: bracketed, plain
    integer :: value
    write(bracketed, fmt=10) 7
    write(plain, fmt=20) 7
    if (bracketed /= '[ 7]' .or. plain /= '   7') error stop 1
    plain = '1234'
    read(plain, fmt=20) value
    if (value /= 1234) error stop 2
10  format('[', i2, ']')
20  format(i4)
end program
