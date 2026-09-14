! rule: R605
! covers: character-literal
! evidence: positive-control
program character_literal_alternative
    implicit none
    character(len=4) :: value
    data value /'Ab c'/

    if (value(1:1) /= 'A') error stop 1
    if (value(2:2) /= 'b') error stop 2
    if (value(3:3) /= ' ') error stop 3
    if (value(4:4) /= 'c') error stop 4
end program character_literal_alternative
