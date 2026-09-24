! rule: S14.2.2-006
! covers: only-list-accesses-listed-entities only-list-hides-unlisted-public-entities
! evidence: effect
! standard: f2023
! oracle-basis: standard
module only_access_provider
  implicit none
  integer :: answer = 42
  integer :: noise = -999
end module
program only_access
  use only_access_provider, only: answer
  implicit none
  integer :: noise, checks
  checks = 0
  noise = -7
  if (answer /= 42) error stop 1
  checks = checks + 1
  if (noise /= -7) error stop 2
  checks = checks + 1
  if (checks /= 2) error stop 3
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 ONLY ACCESS OK'
end program
