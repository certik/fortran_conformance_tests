! rule: C1405
! covers: nonintrinsic-nature-nonintrinsic-module-control
! evidence: effect
! standard: f2023
! oracle-basis: standard
module c1405_provider
  implicit none
  integer :: answer = 42
end module
program nonintrinsic_control
  use, non_intrinsic :: c1405_provider, only: answer
  implicit none
  if (answer /= 42) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 NONINTRINSIC CONTROL OK'
end program
