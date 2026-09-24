program intrinsics_16_9_l_real_binary_4_8_distinct
  use iso_fortran_env, only: real_kinds
  implicit none
  if (.not. any(real_kinds == 4)) stop 77
  if (.not. any(real_kinds == 8)) stop 77
  if (radix(0.0_4) /= 2 .or. radix(0.0_8) /= 2) stop 77
  if (maxexponent(0.0_4) == maxexponent(0.0_8)) stop 77
end program intrinsics_16_9_l_real_binary_4_8_distinct
