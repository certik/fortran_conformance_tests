program i169i_exponent_ieee
  use ieee_arithmetic, only: ieee_value, ieee_positive_inf, ieee_quiet_nan
  implicit none
  real :: inf_value
  real :: nan_value
  inf_value = ieee_value(0.0, ieee_positive_inf)
  nan_value = ieee_value(0.0, ieee_quiet_nan)
  call require_true('exponent ieee infinity huge result', exponent(inf_value) == huge(0))
  call require_true('exponent ieee nan huge result', exponent(nan_value) == huge(0))
  write(*,'(a)') 'INTRINSICS 16.9.I EXPONENT IEEE OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_false(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_false
end program i169i_exponent_ieee
