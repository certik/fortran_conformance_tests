! rule: C1404
! covers: intrinsic-nature-nonintrinsic-module-rejected
! evidence: effect
! standard: f2023
! oracle-basis: standard
module local_env
  implicit none
  integer :: answer = 1
end module
program c1404_intrinsic_nonintrinsic
  use, intrinsic :: local_env, only: answer
  implicit none
end program
