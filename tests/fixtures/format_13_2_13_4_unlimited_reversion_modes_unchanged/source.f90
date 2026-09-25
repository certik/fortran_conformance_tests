! rule: S13.4-008
! covers: unlimited-reversion-modes-unchanged
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_unlimited_reversion_modes_unchanged
  implicit none
  integer :: checks
  character(len=4) :: buf
  checks = 0
  buf = '####'
  write(buf,'(SP,*(I2))') 7,8
  if (len(buf) /= 4) then
    write(*,'(a)') 'F132134:unlimited_reversion_modes_unchanged:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '+7+8') then
    write(*,'(a)') 'F132134:unlimited_reversion_modes_unchanged:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:unlimited_reversion_modes_unchanged:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 UNLIMITED_REVERSION_MODES_UNCHANGED OK'
end program f132134_unlimited_reversion_modes_unchanged
