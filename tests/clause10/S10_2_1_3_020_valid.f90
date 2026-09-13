! rule: S10.2.1.3-020
! covers: fixed-length substring-destination empty-rhs character-array
! F2023 10.2.1.3 p11(2). Default character has a portable blank-padding oracle.
program s10_2_1_3_020_valid
    implicit none
    character(5) :: text, words(2)
    character(7) :: enclosing
    text = 'XXXXX'
    text = 'ab'
    if (text(1:2) /= 'ab' .or. text(3:5) /= '   ') error stop 'fixed-length'
    enclosing = '1234567'
    enclosing(3:5) = 'q'
    if (enclosing /= '12q  67') error stop 'substring-destination'
    text = 'XXXXX'
    text = ''
    if (text /= '     ') error stop 'empty-rhs'
    words = 'XXXXX'
    words = ['ab', 'cd']
    if (words(1) /= 'ab   ' .or. words(2) /= 'cd   ') error stop 'character-array'
end program
