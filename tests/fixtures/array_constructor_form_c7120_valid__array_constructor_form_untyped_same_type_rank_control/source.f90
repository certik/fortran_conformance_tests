program p
implicit none
integer :: vec(2), matrix(2,2)
vec(1) = 11
vec(2) = 13
matrix(1,1) = 17
matrix(2,1) = 19
matrix(1,2) = 23
matrix(2,2) = 29
associate(values => [7,vec,matrix,31])
  if (size(values) /= 8) error stop 1
  if (values(1) /= 7) error stop 2
  if (values(2) /= 11) error stop 3
  if (values(3) /= 13) error stop 4
  if (values(4) /= 17) error stop 5
  if (values(5) /= 19) error stop 6
  if (values(6) /= 23) error stop 7
  if (values(7) /= 29) error stop 8
  if (values(8) /= 31) error stop 9
end associate
end program p
