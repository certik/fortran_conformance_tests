! rule: S7.4.4.3-002
! covers: free-required-graphics
! evidence: effect
! standard: f2023
program character_type_case
implicit none
character(*), parameter :: a = ' A  a '
character(*), parameter :: b = "a  A  "
if (len(a) /= 6 .or. len(b) /= 6) error stop 1
if (a(2:2) == a(5:5)) error stop 2
if (a(2:2) /= b(4:4) .or. a(5:5) /= b(1:1)) error stop 3
if (a(1:1) /= ' ' .or. a(3:4) /= '  ') error stop 4
if (a(6:6) /= ' ' .or. b(2:3) /= '  ') error stop 5
if (b(5:6) /= '  ') error stop 6
end program
