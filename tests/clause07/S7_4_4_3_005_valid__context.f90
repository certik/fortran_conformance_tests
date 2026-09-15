! rule: S7.4.4.3-005
! covers: empty-versus-interior-pair
! evidence: effect
! standard: f2023
program character_type_case
implicit none
character(*), parameter :: a = ''''
character(*), parameter :: q = """"
if (len('') /= 0) error stop 1
if (len(' ') /= 1) error stop 3
if (len('''') /= 1) error stop 5
if (len("") /= 0) error stop 2
if (len(" ") /= 1) error stop 4
if (len("""") /= 1) error stop 6
if (a == ' ' .or. q == ' ' .or. a == q) error stop 7
end program
