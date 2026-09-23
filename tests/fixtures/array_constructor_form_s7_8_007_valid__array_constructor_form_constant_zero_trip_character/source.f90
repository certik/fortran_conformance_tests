program p
implicit none
integer :: i
character(len=2) :: left, right
left = 'AB'
right = 'CD'
associate(equal => [left,right])
  if (len(equal) /= 2) error stop 1
  if (size(equal) /= 2) error stop 2
  if (equal(1) /= 'AB') error stop 3
  if (equal(2) /= 'CD') error stop 4
end associate
associate(zero_constant => [('AB',i=1,0)])
  if (size(zero_constant) /= 0) error stop 5
  if (len(zero_constant) /= 2) error stop 6
end associate
associate(zero_typed => [character(len=3) :: ('AB',i=1,0)])
  if (size(zero_typed) /= 0) error stop 7
  if (len(zero_typed) /= 3) error stop 8
end associate
end program p
