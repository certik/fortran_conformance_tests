! rule: S13.8.1.1-005
! covers: subsequent-editing-replaces
! Expected characters and numeric values are hand-derived from Fortran 2023 clause 13.
program ced_position_t1_subsequent_replacement
  implicit none
  integer :: checks
  character(len=2) :: buf
  checks=0
  buf = repeat('#', len(buf))
  write(buf,'("AB",T1,"C")')
  if (len(buf) /= 2) then
    write(*,'(a)') 'CED:position_t1_subsequent_replacement:observed-length'
    error stop
  end if
  checks=checks+1
  if (buf /= 'CB') then
    write(*,'(a)') 'CED:position_t1_subsequent_replacement:observed-characters'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'CED:position_t1_subsequent_replacement:check-total'
    error stop
  end if
  write(*,'(a)') 'CONTROL EDIT POSITION_T1_SUBSEQUENT_REPLACEMENT OK'
end program ced_position_t1_subsequent_replacement
