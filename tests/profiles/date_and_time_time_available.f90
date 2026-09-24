program date_and_time_time_available
  implicit none
  character(len=10) :: t
  t = '##########'
  call date_and_time(time=t)
  if (t(7:7) /= '.') stop 77
  if (verify(t(1:6)//t(8:10), '0123456789') /= 0) stop 77
end program date_and_time_time_available
