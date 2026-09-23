! rule: S13.8.3-001
! covers: colon-no-effect-with-item
! Expected characters and numeric values are hand-derived from Fortran 2023 clause 13.
program ced_colon_no_effect_with_item
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks=0
  buf = repeat('#', len(buf))
  write(buf,'(I1,:,",",I1)') 4,5
  if (len(buf) /= 3) then
    write(*,'(a)') 'CED:colon_no_effect_with_item:observed-length'
    error stop
  end if
  checks=checks+1
  if (buf /= '4,5') then
    write(*,'(a)') 'CED:colon_no_effect_with_item:observed-characters'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'CED:colon_no_effect_with_item:check-total'
    error stop
  end if
  write(*,'(a)') 'CONTROL EDIT COLON_NO_EFFECT_WITH_ITEM OK'
end program ced_colon_no_effect_with_item
