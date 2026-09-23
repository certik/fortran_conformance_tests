program p
implicit none
associate(slash => (/11,13/))
  if (size(slash) /= 2) error stop 1
  if (slash(1) /= 11) error stop 2
  if (slash(2) /= 13) error stop 3
end associate
associate(square => [11,13])
  if (size(square) /= 2) error stop 4
  if (square(1) /= 11) error stop 5
  if (square(2) /= 13) error stop 6
end associate
end program p
