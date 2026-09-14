! rule: S7.1.5-001
! covers: character-operation
! evidence: effect
program type_basics_character_operation
    implicit none
    character(len=2) :: left = 'AB'
    character(len=3) :: right = 'CDE'

    if (left // right /= 'ABCDE') error stop 1
    if (len(left // right) /= 5) error stop 2
end program type_basics_character_operation
