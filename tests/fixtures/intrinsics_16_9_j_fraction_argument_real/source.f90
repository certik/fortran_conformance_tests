program intrinsics_16_9_j_fraction_argument_real
  implicit none
  integer :: checks
  integer, parameter :: rk = kind(0.0d0)
  real(rk) :: high, expected, observed
  checks=0
  high = 1.0_rk
  expected = 1.0_rk / real(radix(high), kind=rk)
  observed = fraction(high)
  if (observed /= expected) then
    write(*,'(a)') 'I16J:fraction_argument_real:selected-real-x'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (1)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FRACTION ARGUMENT REAL OK'
end program intrinsics_16_9_j_fraction_argument_real
