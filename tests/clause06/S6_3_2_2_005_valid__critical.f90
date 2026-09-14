! rule: S6.3.2.2-005
! covers: end-critical
! evidence: positive-control
! requires: coarray
program critical_spellings
  implicit none
  integer :: value
  value = 0
  critical
    value = 1
  endcritical
  if (value /= 1) stop 1
  critical
    value = value + 1
  end critical
  if (value /= 2) stop 2
end program
