! rule: C1405
! covers: nonintrinsic-nature-intrinsic-module-rejected
! evidence: effect
! standard: f2023
! oracle-basis: standard
program c1405_nonintrinsic_intrinsic
  use, non_intrinsic :: iso_fortran_env, only: input_unit
  implicit none
end program
