! rule: S6.1.2-002
! covers: character-literal-exception
! evidence: effect
program literalcase
    implicit none
    character(len=6) :: apostrophe, quotation

    apostrophe = 'AaZzBb'
    quotation = "aAzZbB"
    if (apostrophe(1:1) /= 'A') error stop 1
    if (apostrophe(2:2) /= 'a') error stop 2
    if (apostrophe(3:3) /= 'Z') error stop 3
    if (apostrophe(4:4) /= 'z') error stop 4
    if (apostrophe(5:5) /= 'B') error stop 5
    if (apostrophe(6:6) /= 'b') error stop 6
    if (quotation(1:1) /= apostrophe(2:2)) error stop 7
    if (quotation(2:2) /= apostrophe(1:1)) error stop 8
    if (quotation(3:3) /= apostrophe(4:4)) error stop 9
    if (quotation(4:4) /= apostrophe(3:3)) error stop 10
    if (quotation(5:5) /= apostrophe(6:6)) error stop 11
    if (quotation(6:6) /= apostrophe(5:5)) error stop 12
    ! Equalities alone would also pass if all literal letters were folded.
    if (apostrophe(1:1) == apostrophe(2:2)) error stop 13
    if (apostrophe(3:3) == apostrophe(4:4)) error stop 14
    if (apostrophe(5:5) == apostrophe(6:6)) error stop 15
end program literalcase
