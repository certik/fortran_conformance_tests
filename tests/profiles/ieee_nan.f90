program ieee_nan
  use, intrinsic :: ieee_arithmetic
  implicit none
  if (.not. ieee_support_datatype(0.0)) stop 77
  if (.not. ieee_support_nan(0.0)) stop 77
end program ieee_nan
