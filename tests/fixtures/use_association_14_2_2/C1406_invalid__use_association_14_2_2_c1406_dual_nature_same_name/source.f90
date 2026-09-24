! rule: C1406
! covers: dual-nature-same-name-reference-rejected
! evidence: effect
! standard: f2023
! oracle-basis: standard
module iso_fortran_env
  implicit none
  integer :: answer = 1
end module
program c1406_dual_nature_same_name
  use, intrinsic :: iso_fortran_env, only: input_unit
  use, non_intrinsic :: iso_fortran_env, only: answer
  implicit none
end program
