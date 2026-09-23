program p
implicit none
integer :: i, j, lower, upper, stride
lower = 1
upper = 5
stride = 2
associate(single => [(i,i=1,3)])
  if (size(single) /= 3) error stop 1
  if (single(1) /= 1) error stop 2
  if (single(2) /= 2) error stop 3
  if (single(3) /= 3) error stop 4
end associate
associate(multiple => [(i,10*i,i=1,2)])
  if (size(multiple) /= 4) error stop 5
  if (multiple(1) /= 1) error stop 6
  if (multiple(2) /= 10) error stop 7
  if (multiple(3) /= 2) error stop 8
  if (multiple(4) /= 20) error stop 9
end associate
associate(nested => [((10*i+j,j=1,2),i=1,2)])
  if (size(nested) /= 4) error stop 10
  if (nested(1) /= 11) error stop 11
  if (nested(2) /= 12) error stop 12
  if (nested(3) /= 21) error stop 13
  if (nested(4) /= 22) error stop 14
end associate
associate(runtime => [(i,i=lower,upper,stride)])
  if (size(runtime) /= 3) error stop 15
  if (runtime(1) /= 1) error stop 16
  if (runtime(2) /= 3) error stop 17
  if (runtime(3) /= 5) error stop 18
end associate
end program p
