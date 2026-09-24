program command_arguments_supported
  implicit none
  integer :: length, status
  length = -7777
  status = -7777
  call get_command_argument(0, length=length, status=status)
  if (status > 0) stop 77
  if (status /= 0 .or. length < 0) error stop
end program command_arguments_supported
