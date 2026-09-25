program ieee_datatype
  use, intrinsic :: ieee_arithmetic
  implicit none
  if (.not. ieee_support_datatype(0.0)) stop 77
end program ieee_datatype
