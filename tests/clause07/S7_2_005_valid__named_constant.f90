! rule: S7.2-005
! covers: named-character-constant
! evidence: effect
program type_parameters_assumed_constant
    implicit none
    character(len=*), parameter :: text = 'AB' // 'C'
    character(len=*), parameter :: padded = 'A ' // 'B  '
    character(len=*), parameter :: empty = ''

    if (len(text) /= 3) error stop 1
    if (text /= 'ABC') error stop 2
    if (len(padded) /= 5) error stop 3
    if (padded /= 'A B  ') error stop 4
    if (len(empty) /= 0) error stop 5
end program type_parameters_assumed_constant
