! rule: S13.4-009
! covers: complete-reversion-modes-unchanged
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_complete_reversion_modes_unchanged
  implicit none
  integer :: checks
  character(len=2) :: rec(2)
  character(len=4) :: observed
  checks = 0
  rec = '#'
  observed = '####'
  write(rec,'(SP,(I2))') 7,8
  observed = rec(1) // rec(2)
  if (len(observed) /= 4) then
    write(*,'(a)') 'F132134:complete_reversion_modes_unchanged:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (observed /= '+7+8') then
    write(*,'(a)') 'F132134:complete_reversion_modes_unchanged:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:complete_reversion_modes_unchanged:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 COMPLETE_REVERSION_MODES_UNCHANGED OK'
end program f132134_complete_reversion_modes_unchanged
