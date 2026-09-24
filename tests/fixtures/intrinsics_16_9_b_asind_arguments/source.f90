program intrinsics_16_9_b_asind_arguments
  implicit none
  integer :: checks
  real :: values(3)
  checks=0
  values = asind([-1.0, 0.0, 1.0])
  if (any(values < -90.0) .or. any(values > 90.0)) then
    write(*,'(a)') 'I16B:asind_arguments:real-boundary-arguments'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (1)
  case default
    write(*,'(a)') 'I16B:asind_arguments:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B ASIND ARGUMENTS OK'
end program intrinsics_16_9_b_asind_arguments
