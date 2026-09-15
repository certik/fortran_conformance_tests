! rule: S7.4.4.3-003
! covers: other-delimiter-data
! evidence: effect
! standard: f2023
program character_type_case
implicit none
character(*), parameter :: a = 'A"B'
character(*), parameter :: b = "A'B"
if (len(a) /= 3 .or. len(b) /= 3) error stop 1
if (a(2:2) /= '"') error stop 2
if (b(2:2) /= "'") error stop 3
if (a(2:2) == b(2:2)) error stop 4
if (a(1:1) /= 'A' .or. a(3:3) /= 'B') error stop 5
if (b(1:1) /= 'A' .or. b(3:3) /= 'B') error stop 6
end program
