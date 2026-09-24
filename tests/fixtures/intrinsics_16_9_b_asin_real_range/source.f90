program intrinsics_16_9_b_asin_real_range
  implicit none
  integer :: checks
  real :: inputs(3), values(3)
  checks=0
  inputs = [-1.0, 0.0, 1.0]
  values = asin(inputs)
  if (any(values < -2.0)) then
    write(*,'(a)') 'I16B:asin_real_range:radian-lower-bound'
    error stop
  end if
  checks=checks+1
  if (any(values > 2.0)) then
    write(*,'(a)') 'I16B:asin_real_range:radian-upper-bound'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16B:asin_real_range:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B ASIN REAL RANGE OK'
end program intrinsics_16_9_b_asin_real_range
