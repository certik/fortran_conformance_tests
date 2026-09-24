program cpu_time_available
  implicit none
  real :: t
  t = -10.0
  call cpu_time(t)
  if (.not. (t >= 0.0)) stop 77
end program cpu_time_available
