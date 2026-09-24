! rule: C1404
! covers: intrinsic-nature-intrinsic-module-control
! evidence: effect
! standard: f2023
! oracle-basis: standard
module c1404_shadow_env
  implicit none
  integer :: input_unit = -777
end module
program intrinsic_control
  use, intrinsic :: iso_fortran_env, only: input_unit
  implicit none
  if (input_unit == -777) error stop 1
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 INTRINSIC CONTROL OK'
end program
