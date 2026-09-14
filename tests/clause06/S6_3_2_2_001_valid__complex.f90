! rule: S6.3.2.2-001
! covers: compound-complex
! evidence: positive-control
program compound_complex_blanks
  implicit none
  complex :: value
  value = ( 2 , - 3 )
  if (real(value) /= 2.0) stop 1
  if (aimag(value) /= -3.0) stop 2
end program
