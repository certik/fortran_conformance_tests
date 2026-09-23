! rule: S13.8.4-001
! covers: SP-sets-plus
! Expected characters and numeric values are hand-derived from Fortran 2023 clause 13.
program ced_sp_prints_optional_plus
  implicit none
  integer :: checks
  character(len=2) :: buf
  checks=0
  buf = repeat('#', len(buf))
  write(buf,'(SP,I2)') 7
  if (len(buf) /= 2) then
    write(*,'(a)') 'CED:sp_prints_optional_plus:observed-length'
    error stop
  end if
  checks=checks+1
  if (buf /= '+7') then
    write(*,'(a)') 'CED:sp_prints_optional_plus:observed-characters'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'CED:sp_prints_optional_plus:check-total'
    error stop
  end if
  write(*,'(a)') 'CONTROL EDIT SP_PRINTS_OPTIONAL_PLUS OK'
end program ced_sp_prints_optional_plus
