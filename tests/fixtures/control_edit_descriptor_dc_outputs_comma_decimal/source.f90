! rule: S13.8.9-001
! covers: DC-sets-comma
! Expected characters and numeric values are hand-derived from Fortran 2023 clause 13.
program ced_dc_outputs_comma_decimal
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks=0
  buf = repeat('#', len(buf))
  write(buf,'(DC,F3.1)') 1.5
  if (len(buf) /= 3) then
    write(*,'(a)') 'CED:dc_outputs_comma_decimal:observed-length'
    error stop
  end if
  checks=checks+1
  if (buf /= '1,5') then
    write(*,'(a)') 'CED:dc_outputs_comma_decimal:observed-characters'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'CED:dc_outputs_comma_decimal:check-total'
    error stop
  end if
  write(*,'(a)') 'CONTROL EDIT DC_OUTPUTS_COMMA_DECIMAL OK'
end program ced_dc_outputs_comma_decimal
