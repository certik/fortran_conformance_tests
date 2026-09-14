! rule: S6.3.2.6-001
! covers: whole-statements continued-statement enclosing-if
! evidence: positive-control
program free_statement_labels
  implicit none
10 integer :: value
20 value = 0
30 value = value + 7
  if (value /= 7) error stop 1
40 value = value + &
    & 2
  if (value /= 9) error stop 2
50 if (.true.) value = value + 3
  if (value /= 12) error stop 3
60 end program
