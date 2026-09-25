! rule: S13.4-009
! covers: reversion-positions-like-slash
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_reversion_positions_like_slash
  implicit none
  integer :: checks
  character(len=1) :: rec(3)
  character(len=3) :: observed
  checks = 0
  rec = '#'
  observed = '###'
  write(rec,'(SS,I1)') 1,2,3
  observed = rec(1) // rec(2) // rec(3)
  if (len(observed) /= 3) then
    write(*,'(a)') 'F132134:reversion_positions_like_slash:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (observed /= '123') then
    write(*,'(a)') 'F132134:reversion_positions_like_slash:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:reversion_positions_like_slash:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 REVERSION_POSITIONS_LIKE_SLASH OK'
end program f132134_reversion_positions_like_slash
