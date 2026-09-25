program p
implicit none
integer :: i
i = 99
associate(values => [(i,i=1,2),(i,i=3,4)])
  if (size(values) /= 4) error stop 1
  if (values(1) /= 1) error stop 2
  if (values(2) /= 2) error stop 3
  if (values(3) /= 3) error stop 4
  if (values(4) /= 4) error stop 5
end associate
if (i /= 99) error stop 6
end program p
