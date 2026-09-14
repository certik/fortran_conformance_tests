! rule: S6.3.2.2-001
! covers: keyword-interior
! evidence: effect
program token_keyword
  implicit none
  inte ger :: value ! {error S6.3.2.2-001}
  value = 7
  if (value /= 7) stop 1
end program
