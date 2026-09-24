program date_and_time_values_4_available
  implicit none
  integer :: v(8)
  v = 123456789
  call date_and_time(values=v)
  if (v(4) == -huge(v(1))) stop 77
end program date_and_time_values_4_available
