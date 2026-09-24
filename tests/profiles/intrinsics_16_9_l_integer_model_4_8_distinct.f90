program intrinsics_16_9_l_integer_model_4_8_distinct
  use iso_fortran_env, only: integer_kinds
  implicit none
  if (.not. any(integer_kinds == 4)) stop 77
  if (.not. any(integer_kinds == 8)) stop 77
  if (digits(0_4) == digits(0_8)) stop 77
end program intrinsics_16_9_l_integer_model_4_8_distinct
