program date_and_time_date_available
  implicit none
  character(len=8) :: d
  d = '########'
  call date_and_time(date=d)
  if (verify(d, '0123456789') /= 0) stop 77
end program date_and_time_date_available
