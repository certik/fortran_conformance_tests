! rule: S13.4-003
! covers: reversion-exception
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_reversion_exception
  implicit none
  integer :: checks
  character(len=1) :: rec(2)
  character(len=2) :: observed
  checks = 0
  rec = '#'
  observed = '##'
  write(rec,'(SS,I1)') 1,2
  observed = rec(1) // rec(2)
  if (len(observed) /= 2) then
    write(*,'(a)') 'F132134:reversion_exception:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (observed /= '12') then
    write(*,'(a)') 'F132134:reversion_exception:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:reversion_exception:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 REVERSION_EXCEPTION OK'
end program f132134_reversion_exception
