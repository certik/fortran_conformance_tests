! rule: S13.4-009
! covers: no-preceding-parenthesis-fallback
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_no_preceding_parenthesis_fallback
  implicit none
  integer :: checks
  character(len=2) :: rec(3)
  character(len=6) :: observed
  checks = 0
  rec = '#'
  observed = '######'
  write(rec,'(SS,"H",I1)') 1,2,3
  observed = rec(1) // rec(2) // rec(3)
  if (len(observed) /= 6) then
    write(*,'(a)') 'F132134:no_preceding_parenthesis_fallback:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (observed /= 'H1H2H3') then
    write(*,'(a)') 'F132134:no_preceding_parenthesis_fallback:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:no_preceding_parenthesis_fallback:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 NO_PRECEDING_PARENTHESIS_FALLBACK OK'
end program f132134_no_preceding_parenthesis_fallback
