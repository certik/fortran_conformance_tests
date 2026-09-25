program ieee_status_overflow_rounding
  use, intrinsic :: ieee_arithmetic
  implicit none
  if (.not. ieee_support_flag(ieee_overflow, 0.0)) stop 77
  if (.not. ieee_support_rounding(ieee_nearest, 0.0)) stop 77
  if (.not. ieee_support_rounding(ieee_to_zero, 0.0)) stop 77
  if (ieee_support_halting(ieee_overflow)) call ieee_set_halting_mode(ieee_overflow, .false.)
end program ieee_status_overflow_rounding
