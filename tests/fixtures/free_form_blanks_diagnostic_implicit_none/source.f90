! rule: S6.3.2.2-004
! covers: implicit-none
! evidence: effect
program required_keyword_separator
  implicitnone ! {error S6.3.2.2-004}
  integer :: value
  value = 7
  if (value /= 7) stop 1
end program
