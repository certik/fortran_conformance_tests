! rule: C731
! covers: statement-function-length statement-dummy-length
! evidence: positive-control
! standard: f2023
program character_type_case
implicit none
character(2) :: f, x
f(x) = x
if (len(f('AB')) /= 2) error stop 1
if (f('AB') /= 'AB') error stop 2
if (f('xy') /= 'xy') error stop 3
end program
