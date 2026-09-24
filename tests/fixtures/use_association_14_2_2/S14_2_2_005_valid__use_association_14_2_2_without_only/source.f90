! rule: S14.2.2-005
! covers: use-without-only-accesses-all-public-entities
! evidence: effect
! standard: f2023
! oracle-basis: standard
module all_public_provider
  implicit none
  integer :: first = 41
  integer :: second = 42
  integer, private :: hidden = -999
end module
program without_only
  use all_public_provider
  implicit none
  if (first + second /= 83) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 WITHOUT ONLY OK'
end program
