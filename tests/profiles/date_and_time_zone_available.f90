program date_and_time_zone_available
  implicit none
  character(len=5) :: z
  z = '#####'
  call date_and_time(zone=z)
  if (.not. (z(1:1) == '+' .or. z(1:1) == '-')) stop 77
  if (verify(z(2:5), '0123456789') /= 0) stop 77
end program date_and_time_zone_available
