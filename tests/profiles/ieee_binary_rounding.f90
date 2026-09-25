program ieee_binary_rounding
  use, intrinsic :: ieee_arithmetic
  implicit none
  if (radix(0.0) /= 2) stop 77
  if (.not. ieee_support_datatype(0.0)) stop 77
  if (.not. ieee_support_rounding(ieee_nearest, 0.0)) stop 77
  if (.not. ieee_support_rounding(ieee_to_zero, 0.0)) stop 77
  if (.not. ieee_support_rounding(ieee_up, 0.0)) stop 77
  if (.not. ieee_support_rounding(ieee_down, 0.0)) stop 77
end program ieee_binary_rounding
