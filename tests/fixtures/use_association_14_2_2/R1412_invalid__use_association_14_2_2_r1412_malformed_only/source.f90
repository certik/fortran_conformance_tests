! rule: R1412
! covers: malformed-only-item-rejected
! evidence: effect
! standard: f2023
! oracle-basis: standard
module r1412_diag_provider
  implicit none
  integer :: answer = 1
end module
program r1412_malformed_only
  use r1412_diag_provider, only: => answer
  implicit none
end program
