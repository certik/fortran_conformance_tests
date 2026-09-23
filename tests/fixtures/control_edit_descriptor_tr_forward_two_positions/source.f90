! rule: S13.8.1.2-004
! covers: TR-forward
! Expected characters and numeric values are hand-derived from Fortran 2023 clause 13.
program ced_tr_forward_two_positions
  implicit none
  integer :: checks
  character(len=4) :: buf
  checks=0
  buf = repeat('#', len(buf))
  write(buf,'("A",TR2,"B")')
  if (len(buf) /= 4) then
    write(*,'(a)') 'CED:tr_forward_two_positions:observed-length'
    error stop
  end if
  checks=checks+1
  if (buf /= 'A  B') then
    write(*,'(a)') 'CED:tr_forward_two_positions:observed-characters'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'CED:tr_forward_two_positions:check-total'
    error stop
  end if
  write(*,'(a)') 'CONTROL EDIT TR_FORWARD_TWO_POSITIONS OK'
end program ced_tr_forward_two_positions
