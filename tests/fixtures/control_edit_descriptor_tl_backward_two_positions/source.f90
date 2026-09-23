! rule: S13.8.1.2-003
! covers: TL-backward
! Expected characters and numeric values are hand-derived from Fortran 2023 clause 13.
program ced_tl_backward_two_positions
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks=0
  buf = repeat('#', len(buf))
  write(buf,'("ABC",TL2,"Z")')
  if (len(buf) /= 3) then
    write(*,'(a)') 'CED:tl_backward_two_positions:observed-length'
    error stop
  end if
  checks=checks+1
  if (buf /= 'AZC') then
    write(*,'(a)') 'CED:tl_backward_two_positions:observed-characters'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'CED:tl_backward_two_positions:check-total'
    error stop
  end if
  write(*,'(a)') 'CONTROL EDIT TL_BACKWARD_TWO_POSITIONS OK'
end program ced_tl_backward_two_positions
