program ieee_exceptional_all
  use, intrinsic :: ieee_arithmetic
  implicit none
  if (.not. ieee_support_datatype(0.0)) stop 77
  if (.not. ieee_support_nan(0.0)) stop 77
  if (.not. ieee_support_inf(0.0)) stop 77
  if (.not. ieee_support_subnormal(0.0)) stop 77
end program ieee_exceptional_all
