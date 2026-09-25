! rule: S13.4-008
! covers: unlimited-reversion-no-record-positioning
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_unlimited_reversion_no_record_positioning
  implicit none
  integer :: checks
  character(len=5) :: buf
  checks = 0
  buf = '#####'
  write(buf,'(SS,*(I1,:,","))') 4,5,6
  if (len(buf) /= 5) then
    write(*,'(a)') 'F132134:unlimited_reversion_no_record_positioning:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '4,5,6') then
    write(*,'(a)') 'F132134:unlimited_reversion_no_record_positioning:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:unlimited_reversion_no_record_positioning:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 UNLIMITED_REVERSION_NO_RECORD_POSITIONING OK'
end program f132134_unlimited_reversion_no_record_positioning
