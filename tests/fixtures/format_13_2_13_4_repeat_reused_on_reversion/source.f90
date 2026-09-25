! rule: S13.4-009
! covers: repeat-reused-on-reversion
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_repeat_reused_on_reversion
  implicit none
  integer :: checks
  character(len=3) :: rec(3)
  character(len=9) :: observed
  checks = 0
  rec = '#'
  observed = '#########'
  write(rec,'(SS,"H",2(I1))') 1,2,3,4,5,6
  observed = rec(1) // rec(2) // rec(3)
  if (len(observed) /= 9) then
    write(*,'(a)') 'F132134:repeat_reused_on_reversion:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (observed /= 'H1234 56 ') then
    write(*,'(a)') 'F132134:repeat_reused_on_reversion:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:repeat_reused_on_reversion:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 REPEAT_REUSED_ON_REVERSION OK'
end program f132134_repeat_reused_on_reversion
