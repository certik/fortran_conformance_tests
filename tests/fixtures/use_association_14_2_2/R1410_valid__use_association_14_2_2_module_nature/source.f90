! rule: R1410
! covers: module-nature-intrinsic module-nature-nonintrinsic
! evidence: effect
! standard: f2023
! oracle-basis: standard
module r1410_provider
  implicit none
  integer :: answer = 42
end module
module r1410_shadow_env
  implicit none
  integer :: input_unit = -777
end module
program module_nature_forms
  use, intrinsic :: iso_fortran_env, only: input_unit
  use, non_intrinsic :: r1410_provider, only: answer
  implicit none
  integer :: checks
  checks = 0
  if (input_unit == -777) error stop 1
  checks = checks + 1
  if (answer /= 42) error stop 2
  checks = checks + 1
  if (checks /= 2) error stop 3
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 MODULE NATURE OK'
end program
