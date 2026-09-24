program intrinsics_16_9_b_asind_degree_range
  implicit none
  integer :: checks
  real :: inputs(3), values(3)
  checks=0
  inputs = [-1.0, 0.0, 1.0]
  values = asind(inputs)
  if (any(values < -90.0)) then
    write(*,'(a)') 'I16B:asind_degree_range:degree-lower-bound'
    error stop
  end if
  checks=checks+1
  if (any(values > 90.0)) then
    write(*,'(a)') 'I16B:asind_degree_range:degree-upper-bound'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16B:asind_degree_range:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B ASIND DEGREE RANGE OK'
end program intrinsics_16_9_b_asind_degree_range
