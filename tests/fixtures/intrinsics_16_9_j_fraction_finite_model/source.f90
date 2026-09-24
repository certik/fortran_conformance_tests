program intrinsics_16_9_j_fraction_finite_model
  implicit none
  integer :: checks
  integer, parameter :: rk = kind(0.0d0)
  real(rk) :: one, radix_power, expected, observed_one, observed_power
  checks=0
  one = 1.0_rk
  radix_power = real(radix(one), kind=rk)
  expected = 1.0_rk / real(radix(one), kind=rk)
  observed_one = fraction(one)
  if (observed_one /= expected) then
    write(*,'(a)') 'I16J:fraction_finite_model:one-model-value'
    error stop
  end if
  checks=checks+1
  observed_power = fraction(radix_power)
  if (observed_power /= expected) then
    write(*,'(a)') 'I16J:fraction_finite_model:radix-power-model-value'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FRACTION FINITE MODEL OK'
end program intrinsics_16_9_j_fraction_finite_model
