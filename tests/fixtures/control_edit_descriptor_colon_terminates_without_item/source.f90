! rule: S13.8.3-001
! covers: colon-terminates-without-item
! Expected characters and numeric values are hand-derived from Fortran 2023 clause 13.
program ced_colon_terminates_without_item
  implicit none
  integer :: checks
  character(len=1) :: buf
  checks=0
  buf = repeat('#', len(buf))
  write(buf,'(I1,:,",",I1)') 4
  if (len(buf) /= 1) then
    write(*,'(a)') 'CED:colon_terminates_without_item:observed-length'
    error stop
  end if
  checks=checks+1
  if (buf /= '4') then
    write(*,'(a)') 'CED:colon_terminates_without_item:observed-characters'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'CED:colon_terminates_without_item:check-total'
    error stop
  end if
  write(*,'(a)') 'CONTROL EDIT COLON_TERMINATES_WITHOUT_ITEM OK'
end program ced_colon_terminates_without_item
