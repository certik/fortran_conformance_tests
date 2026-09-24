program ieee_flags_all
  use, intrinsic :: ieee_arithmetic
  implicit none
  call require_flag(ieee_overflow)
  call require_flag(ieee_divide_by_zero)
  call require_flag(ieee_invalid)
  call require_flag(ieee_underflow)
  call require_flag(ieee_inexact)
contains
  subroutine require_flag(flag)
    type(ieee_flag_type), intent(in) :: flag
    logical :: halting
    if (.not. ieee_support_datatype(0.0)) stop 77
    if (.not. ieee_support_flag(flag, 0.0)) stop 77
    if (.not. ieee_support_halting(flag)) then
      call ieee_get_halting_mode(flag, halting)
      if (halting) stop 77
    end if
  end subroutine require_flag
end program ieee_flags_all
