! rule: S13.8.1.2-002
! covers: T-forward-from-current
! Expected characters and numeric values are hand-derived from Fortran 2023 clause 13.
program ced_t_forward_from_current
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks=0
  buf = repeat('#', len(buf))
  write(buf,'("A",T3,"B")')
  if (len(buf) /= 3) then
    write(*,'(a)') 'CED:t_forward_from_current:observed-length'
    error stop
  end if
  checks=checks+1
  if (buf /= 'A B') then
    write(*,'(a)') 'CED:t_forward_from_current:observed-characters'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'CED:t_forward_from_current:check-total'
    error stop
  end if
  write(*,'(a)') 'CONTROL EDIT T_FORWARD_FROM_CURRENT OK'
end program ced_t_forward_from_current
