program ieee_flag_invalid_nan
  use, intrinsic :: ieee_arithmetic
  implicit none
  call require_flag(ieee_invalid)
  if (.not. ieee_support_nan(0.0)) stop 77
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
end program ieee_flag_invalid_nan
