! rule: S14.2.2-003
! covers: module-identifiers-identify-accessed-entities default-use-keeps-same-identifier rename-local-identifier-refers-to-module-entity
! evidence: effect
! standard: f2023
! oracle-basis: standard
module s1422_003_provider
  implicit none
  integer :: module_value = 42
  integer :: hidden = 51
  integer :: other = -999
end module
program use_assoc_identifier_forms
  use s1422_003_provider, only: module_value, local_hidden => hidden
  implicit none
  integer :: checks, hidden, other
  checks = 0
  hidden = -7
  other = -8
  if (module_value /= 42) error stop 1
  checks = checks + 1
  if (module_value + 0 /= 42) error stop 2
  checks = checks + 1
  if (local_hidden /= 51 .or. hidden /= -7 .or. other /= -8) error stop 3
  checks = checks + 1
  if (checks /= 3) error stop 4
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 IDENTIFIER FORMS OK'
end program
