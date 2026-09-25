program ieee_sqrt_all
  use, intrinsic :: ieee_arithmetic
  implicit none
  if (.not. ieee_support_datatype(0.0)) stop 77
  if (.not. ieee_support_sqrt(0.0)) stop 77
  if (.not. ieee_support_nan(0.0)) stop 77
  if (.not. ieee_support_inf(0.0)) stop 77
  if (.not. ieee_support_subnormal(0.0)) stop 77
  if (ieee_support_underflow_control(0.0)) call ieee_set_underflow_mode(.true.)
end program ieee_sqrt_all
