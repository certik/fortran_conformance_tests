program intrinsics_16_9_b_asin_arguments
  implicit none
  integer :: checks
  real :: real_values(3)
  complex :: z, z_value
  checks=0
  real_values = asin([-1.0, 0.0, 1.0])
  z = (0.5, 0.75)
  z_value = asin(z)
  if (any(real_values < -2.0) .or. any(real_values > 2.0)) then
    write(*,'(a)') 'I16B:asin_arguments:real-boundary-arguments'
    error stop
  end if
  checks=checks+1
  if (real(z_value) < -2.0 .or. real(z_value) > 2.0) then
    write(*,'(a)') 'I16B:asin_arguments:complex-argument'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16B:asin_arguments:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B ASIN ARGUMENTS OK'
end program intrinsics_16_9_b_asin_arguments
