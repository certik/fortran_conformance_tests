program intrinsics_16_9_b_asin_complex_range
  implicit none
  integer :: checks
  complex :: z, z_value
  real :: part
  checks=0
  z = (0.5, 0.75)
  z_value = asin(z)
  part = real(z_value)
  if (part < -2.0) then
    write(*,'(a)') 'I16B:asin_complex_range:complex-real-lower'
    error stop
  end if
  checks=checks+1
  if (part > 2.0) then
    write(*,'(a)') 'I16B:asin_complex_range:complex-real-upper'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16B:asin_complex_range:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B ASIN COMPLEX RANGE OK'
end program intrinsics_16_9_b_asin_complex_range
