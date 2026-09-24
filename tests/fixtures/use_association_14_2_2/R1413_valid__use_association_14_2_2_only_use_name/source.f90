! rule: R1413
! covers: only-use-name-designates-module-name
! evidence: effect
! standard: f2023
! oracle-basis: standard
module r1413_provider
  implicit none
  integer :: answer = 42
end module
program only_use_name
  use r1413_provider, only: answer
  implicit none
  if (answer /= 42) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 ONLY USE NAME OK'
end program
