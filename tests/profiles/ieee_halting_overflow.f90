program ieee_halting_overflow
  use, intrinsic :: ieee_arithmetic
  implicit none
  if (.not. ieee_support_halting(ieee_overflow)) stop 77
  call ieee_set_halting_mode(ieee_overflow, .false.)
end program ieee_halting_overflow
