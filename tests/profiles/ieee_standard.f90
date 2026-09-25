program ieee_standard
  use, intrinsic :: ieee_arithmetic
  implicit none
  if (.not. ieee_support_standard(0.0)) stop 77
end program ieee_standard
