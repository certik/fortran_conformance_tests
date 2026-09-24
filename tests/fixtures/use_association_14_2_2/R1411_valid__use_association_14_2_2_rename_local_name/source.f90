! rule: R1411
! covers: rename-local-name-form
! evidence: effect
! standard: f2023
! oracle-basis: standard
module r1411_provider
  implicit none
  integer :: original = 42
  integer :: wrong = -999
end module
program rename_local_name
  use r1411_provider, local_name => original
  implicit none
  integer :: original, checks
  checks = 0
  original = -7
  if (local_name /= 42 .or. original /= -7) error stop 1
  checks = checks + 1
  if (checks /= 1) error stop 2
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 RENAME LOCAL NAME OK'
end program
