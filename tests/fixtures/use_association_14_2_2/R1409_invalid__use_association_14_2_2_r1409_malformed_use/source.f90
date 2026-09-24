! rule: R1409
! covers: malformed-use-stmt-rejected
! evidence: effect
! standard: f2023
! oracle-basis: standard
module r1409_diag_provider
  implicit none
  integer :: answer = 1
end module
program r1409_malformed_use
  use, only: answer
  implicit none
end program
