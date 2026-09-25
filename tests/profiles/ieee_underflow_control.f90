program ieee_underflow_control
  use, intrinsic :: ieee_arithmetic
  implicit none
  logical :: halting
  if (.not. ieee_support_datatype(0.0)) stop 77
  if (.not. ieee_support_underflow_control(0.0)) stop 77
  if (.not. ieee_support_subnormal(0.0)) stop 77
  if (ieee_support_flag(ieee_underflow, 0.0)) then
    if (ieee_support_halting(ieee_underflow)) then
      call ieee_set_halting_mode(ieee_underflow, .false.)
    else
      call ieee_get_halting_mode(ieee_underflow, halting)
      if (halting) stop 77
    end if
  end if
end program ieee_underflow_control
