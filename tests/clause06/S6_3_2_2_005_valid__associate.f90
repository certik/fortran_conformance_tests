! rule: S6.3.2.2-005
! covers: end-associate
! evidence: positive-control
program associate_spellings
  implicit none
  integer :: value
  associate (n => 2)
    value = n
  endassociate
  if (value /= 2) stop 1
  associate (n => 3)
    value = value + n
  end associate
  if (value /= 5) stop 2
end program
