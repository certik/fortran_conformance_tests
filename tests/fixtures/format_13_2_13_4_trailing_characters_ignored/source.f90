! rule: S13.2.2-002
! covers: trailing-characters-ignored
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_trailing_characters_ignored
  implicit none
  integer :: checks
  character(len=9) :: fmt_a, fmt_b
  character(len=3) :: a, b
  character(len=6) :: observed
  checks = 0
  fmt_a = '(SS,I3)AB'
  fmt_b = '(SS,I3)WX'
  a = '###'
  b = '###'
  observed = '######'
  write(a,fmt_a) 7
  write(b,fmt_b) 7
  observed = a // b
  if (len(observed) /= 6) then
    write(*,'(a)') 'F132134:trailing_characters_ignored:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (observed /= '  7  7') then
    write(*,'(a)') 'F132134:trailing_characters_ignored:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:trailing_characters_ignored:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 TRAILING_CHARACTERS_IGNORED OK'
end program f132134_trailing_characters_ignored
