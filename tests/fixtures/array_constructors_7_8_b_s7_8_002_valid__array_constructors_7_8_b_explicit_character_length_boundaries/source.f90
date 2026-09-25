program p
implicit none
associate(empty => [character(len=3) ::])
  if (size(empty) /= 0) error stop 1
  if (len(empty) /= 3) error stop 2
end associate
associate(values => [character(len=3) :: 'ab','abcd'])
  if (len(values) /= 3) error stop 3
  if (size(values) /= 2) error stop 4
  if (values(1) /= 'ab ') error stop 5
  if (values(2) /= 'abc') error stop 6
end associate
end program p
