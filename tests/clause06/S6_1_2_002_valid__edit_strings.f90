! rule: S6.1.2-002
! covers: character-string-edit-exception
! evidence: effect
program editstringcase
    implicit none
    character(len=4) :: apostrophe, quotation
    integer :: status

    apostrophe = '????'
    quotation = '????'
    write(apostrophe, 100, iostat=status)
    if (status /= 0) error stop 1
    write(quotation, 200, iostat=status)
    if (status /= 0) error stop 2
100 format('AaZz')
200 FORMAT("BbYy")
    if (apostrophe(1:1) /= 'A') error stop 3
    if (apostrophe(2:2) /= 'a') error stop 4
    if (apostrophe(3:3) /= 'Z') error stop 5
    if (apostrophe(4:4) /= 'z') error stop 6
    if (quotation(1:1) /= 'B') error stop 7
    if (quotation(2:2) /= 'b') error stop 8
    if (quotation(3:3) /= 'Y') error stop 9
    if (quotation(4:4) /= 'y') error stop 10
    if (apostrophe(1:1) == apostrophe(2:2)) error stop 11
    if (apostrophe(3:3) == apostrophe(4:4)) error stop 12
    if (quotation(1:1) == quotation(2:2)) error stop 13
    if (quotation(3:3) == quotation(4:4)) error stop 14
end program editstringcase
