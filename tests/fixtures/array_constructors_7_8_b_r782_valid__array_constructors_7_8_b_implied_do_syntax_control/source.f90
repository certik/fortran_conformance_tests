program p
implicit none
integer :: i
associate(values => [(7, i=1,2)])
  if (size(values) /= 2) error stop 1
  if (values(1) /= 7) error stop 2
  if (values(2) /= 7) error stop 3
end associate
end program p
