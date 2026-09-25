program c_long_double_positive
  use, intrinsic :: iso_c_binding, only: c_long_double
  implicit none
  if (c_long_double < 0) stop 77
end program
