! rule: C1406
! covers: single-nature-module-reference-control
! evidence: effect
! standard: f2023
! oracle-basis: standard
module c1406_shadow_env
  implicit none
  integer :: input_unit = -777
end module
program single_nature_control
  use, intrinsic :: iso_fortran_env, only: input_unit
  implicit none
  if (input_unit == -777) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 SINGLE NATURE CONTROL OK'
end program
