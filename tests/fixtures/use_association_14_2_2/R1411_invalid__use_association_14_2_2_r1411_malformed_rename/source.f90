! rule: R1411
! covers: malformed-rename-rejected
! evidence: effect
! standard: f2023
! oracle-basis: standard
module r1411_diag_provider
  implicit none
  integer :: original = 1
end module
program r1411_malformed_rename
  use r1411_diag_provider, local_name = original
  implicit none
end program
