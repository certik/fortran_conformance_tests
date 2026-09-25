program ieee_inf
  use, intrinsic :: ieee_arithmetic
  implicit none
  if (.not. ieee_support_datatype(0.0)) stop 77
  if (.not. ieee_support_inf(0.0)) stop 77
end program ieee_inf
