program main
  implicit none
  integer :: i = 37
  real :: r = 2.5
  logical :: flag = .true.
  character(len=3) :: word = 'xyz'
  integer :: arr(3) = [4,5,6]
  if (i /= 37) error stop
  if (r /= 2.5) error stop
  if (.not. flag) error stop
  if (len(word) /= 3) error stop
  if (word /= 'xyz') error stop
  if (any(arr /= [4,5,6])) error stop
  print '(a)', 'type_declaration s004 initializer values ok'
end program main
