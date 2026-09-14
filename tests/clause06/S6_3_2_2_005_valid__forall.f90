! rule: S6.3.2.2-005
! covers: end-forall
! evidence: positive-control
program forall_spellings
  implicit none
  integer :: i, values(2)
  values = 0
  forall (i = 1:2)
    values(i) = i
  endforall
  if (any(values /= [1, 2])) stop 1
  forall (i = 1:2)
    values(i) = values(i) + 1
  end forall
  if (any(values /= [2, 3])) stop 2
end program
