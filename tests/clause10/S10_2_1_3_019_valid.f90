! rule: S10.2.1.3-019
! covers: fixed-length substring-destination zero-length-destination character-array equal-length-control
! F2023 10.2.1.3 p11(1).
program s10_2_1_3_019_valid
    implicit none
    character(3) :: short, words(2)
    character(7) :: enclosing
    character(0) :: empty
    short = 'abcdef'
    if (short /= 'abc') error stop 'fixed-length'
    enclosing = '1234567'
    enclosing(3:5) = 'wxyz'
    if (enclosing /= '12wxy67') error stop 'substring-destination'
    empty = 'abc'
    if (len(empty) /= 0) error stop 'zero-length-destination'
    words = ['abcde', 'vwxyz']
    if (words(1) /= 'abc' .or. words(2) /= 'vwx') error stop 'character-array'
    short = 'xyz'
    if (short /= 'xyz') error stop 'equal-length-control'
end program
