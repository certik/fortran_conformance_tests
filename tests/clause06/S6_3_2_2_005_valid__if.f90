! rule: S6.3.2.2-005
! covers: else-if end-if
! evidence: positive-control
program if_spellings
  implicit none
  integer :: value
  value = 0
  if (.false.) then
    value = -1
  elseif (.true.) then
    value = 11
  endif
  if (value /= 11) stop 1
  if (.false.) then
    value = -1
  else if (.true.) then
    value = 12
  end if
  if (value /= 12) stop 2
  if (.false.) then
    value = -1
  else   if (.true.) then
    value = 13
  end   if
  if (value /= 13) stop 3
end program
