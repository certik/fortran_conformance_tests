! rule: S7.2-001
! covers: character-length-values concatenation-length
! evidence: effect
program type_parameters_character_effects
    implicit none
    character(len=0) :: empty = ''
    character(len=2) :: short = 'AB'
    character(len=4) :: long = 'CDEF'

    if (len(empty) /= 0) error stop 1
    if (len(short) /= 2) error stop 2
    if (len(long) /= 4) error stop 3
    if (short /= 'AB') error stop 4
    if (long /= 'CDEF') error stop 5
    if (len(short // long) /= 6) error stop 6
    if (short // long /= 'ABCDEF') error stop 7
    if (len(empty // short) /= 2) error stop 8
    if (empty // short /= 'AB') error stop 9
end program type_parameters_character_effects
