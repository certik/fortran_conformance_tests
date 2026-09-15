! rule: S7.4.4.2-002
! covers: letter-values digit-values underscore-value special-character-values
! evidence: effect
! standard: f2023
program character_type_case
implicit none
character(*), parameter :: upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
character(*), parameter :: lower = 'abcdefghijklmnopqrstuvwxyz'
character(*), parameter :: digits = '0123456789'
character(*), parameter :: special = ' =+-*/\()[]{},.:;!"%&~<>?''`^|$#@'
character(*), parameter :: repertoire = upper // lower // digits // '_' // special
integer :: i, j
if (len(upper) /= 26 .or. len(lower) /= 26) error stop 1
if (len(digits) /= 10 .or. len(special) /= 32) error stop 2
if (len(repertoire) /= 95) error stop 3
do i = 1, 95
    do j = i + 1, 95
        if (repertoire(i:i) == repertoire(j:j)) error stop 4
    end do
end do
end program
