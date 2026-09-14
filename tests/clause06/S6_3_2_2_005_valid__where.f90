! rule: S6.3.2.2-005
! covers: else-where end-where
! evidence: positive-control
program where_spellings
  implicit none
  integer :: values(2)
  logical :: mask(2)
  mask = [.true., .false.]
  values = 0
  where (mask)
    values = 1
  elsewhere
    values = 2
  endwhere
  if (any(values /= [1, 2])) stop 1
  where (mask)
    values = values + 2
  else where
    values = values + 3
  end where
  if (any(values /= [3, 5])) stop 2
end program
