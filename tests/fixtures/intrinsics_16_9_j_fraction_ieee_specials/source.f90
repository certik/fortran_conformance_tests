program intrinsics_16_9_j_fraction_ieee_specials
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  real :: qnan, pinf, nan_result, inf_result
  checks=0
  qnan = ieee_value(0.0, ieee_quiet_nan)
  pinf = ieee_value(0.0, ieee_positive_inf)
  nan_result = fraction(qnan)
  if (.not. ieee_is_nan(nan_result)) then
    write(*,'(a)') 'I16J:fraction_ieee_specials:nan-remains-nan'
    error stop
  end if
  checks=checks+1
  inf_result = fraction(pinf)
  if (.not. ieee_is_nan(inf_result)) then
    write(*,'(a)') 'I16J:fraction_ieee_specials:infinity-yields-nan'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FRACTION IEEE SPECIALS OK'
end program intrinsics_16_9_j_fraction_ieee_specials
