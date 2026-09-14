! rule: S6.3.2.2-001
! covers: inter-token
! evidence: positive-control
program inter_token_blanks
  implicit none
  integer :: value
  value = ( 2 + 3 ) * 4
  if ( value /= 20 ) stop 1
end program
