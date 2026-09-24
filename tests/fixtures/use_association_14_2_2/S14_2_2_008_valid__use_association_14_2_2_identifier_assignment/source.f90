! rule: S14.2.2-008
! covers: only-use-name-retains-module-identifier rename-creates-local-identifier unrenamed-entity-keeps-module-identifier multiple-local-identifiers-same-entity
! evidence: effect
! standard: f2023
! oracle-basis: standard
module id_assign_provider
  implicit none
  integer :: answer = 42
  integer :: bonus = 1
  integer :: shared = 5
end module
program identifier_assignment
  use id_assign_provider, only: answer
  use id_assign_provider, local_bonus => bonus
  use id_assign_provider, a => shared, b => shared
  implicit none
  integer :: checks
  checks = 0
  if (answer /= 42) error stop 1
  checks = checks + 1
  if (local_bonus /= 1) error stop 2
  checks = checks + 1
  if (answer + local_bonus /= 43) error stop 3
  checks = checks + 1
  a = 77
  if (b /= 77) error stop 4
  checks = checks + 1
  if (checks /= 4) error stop 5
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 IDENTIFIER ASSIGNMENT OK'
end program
