! rule: S13.8.9-001
! covers: DP-sets-point
! Expected characters and numeric values are hand-derived from Fortran 2023 clause 13.
program ced_dp_outputs_point_decimal
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks=0
  buf = repeat('#', len(buf))
  write(buf,'(DP,F3.1)') 1.5
  if (len(buf) /= 3) then
    write(*,'(a)') 'CED:dp_outputs_point_decimal:observed-length'
    error stop
  end if
  checks=checks+1
  if (buf /= '1.5') then
    write(*,'(a)') 'CED:dp_outputs_point_decimal:observed-characters'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'CED:dp_outputs_point_decimal:check-total'
    error stop
  end if
  write(*,'(a)') 'CONTROL EDIT DP_OUTPUTS_POINT_DECIMAL OK'
end program ced_dp_outputs_point_decimal
