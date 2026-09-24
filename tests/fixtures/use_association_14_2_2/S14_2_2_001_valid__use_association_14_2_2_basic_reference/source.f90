! rule: S14.2.2-001
! covers: use-stmt-specifies-use-association use-stmt-references-module
! evidence: effect
! standard: f2023
! oracle-basis: standard
module s1422_001_provider
  implicit none
  integer :: answer = 42
end module
module s1422_001_wrong_provider
  implicit none
  integer :: answer = -999
end module
program use_assoc_basic_reference
  use s1422_001_provider, only: answer
  implicit none
  integer :: observed, checks
  checks = 0
  observed = -777
  observed = answer
  if (observed /= 42) error stop 1
  checks = checks + 1
  if (answer /= 42) error stop 2
  checks = checks + 1
  if (checks /= 2) error stop 3
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 BASIC REFERENCE OK'
end program
