program p
implicit none
integer :: i
i = 77
associate(values => [(7,1=2,4)])
  if (size(values) /= 3) error stop 1
  if (values(1) /= 7) error stop 2
  if (values(2) /= 7) error stop 3
  if (values(3) /= 7) error stop 4
end associate
if (i /= 77) error stop 5
end program p
