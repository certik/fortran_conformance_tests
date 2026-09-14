! rule: S6.3.2.2-005
! covers: end-program
! evidence: positive-control
program compact_program
  implicit none
  integer :: value
  value = 7
  if (value /= 7) stop 1
endprogram compact_program
