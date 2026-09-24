! rule: R1413
! covers: invalid-only-use-name-rejected
! evidence: effect
! standard: f2023
! oracle-basis: standard
module r1413_diag_provider
  implicit none
  integer :: answer = 1
end module
program r1413_invalid_only_use_name
  use r1413_diag_provider, only: 123
  implicit none
end program
