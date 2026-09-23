! rule: S13.8.1.1-004
! covers: skipped-output-filled-with-blanks
! Expected characters and numeric values are hand-derived from Fortran 2023 clause 13.
program ced_position_t3_writes_later_blank_fill
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks=0
  buf = repeat('#', len(buf))
  write(buf,'(T3,"Z")')
  if (len(buf) /= 3) then
    write(*,'(a)') 'CED:position_t3_writes_later_blank_fill:observed-length'
    error stop
  end if
  checks=checks+1
  if (buf /= '  Z') then
    write(*,'(a)') 'CED:position_t3_writes_later_blank_fill:observed-characters'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'CED:position_t3_writes_later_blank_fill:check-total'
    error stop
  end if
  write(*,'(a)') 'CONTROL EDIT POSITION_T3_WRITES_LATER_BLANK_FILL OK'
end program ced_position_t3_writes_later_blank_fill
