program p
implicit none
associate(ints => [integer :: 1, 2.0, (3.0,0.0)])
  if (size(ints) /= 3) error stop 1
  if (ints(1) /= 1) error stop 2
  if (ints(2) /= 2) error stop 3
  if (ints(3) /= 3) error stop 4
end associate
associate(reals => [real :: 1, 2.0, (3.0,0.0)])
  if (size(reals) /= 3) error stop 5
  if (reals(1) /= 1.0) error stop 6
  if (reals(2) /= 2.0) error stop 7
  if (reals(3) /= 3.0) error stop 8
end associate
associate(complexes => [complex :: 1, 2.0, (3.0,-4.0)])
  if (size(complexes) /= 3) error stop 9
  if (complexes(1) /= (1.0,0.0)) error stop 10
  if (complexes(2) /= (2.0,0.0)) error stop 11
  if (complexes(3) /= (3.0,-4.0)) error stop 12
end associate
associate(logicals => [logical :: .true., .false.])
  if (size(logicals) /= 2) error stop 13
  if (.not. logicals(1)) error stop 14
  if (logicals(2)) error stop 15
end associate
associate(chars => [character(len=2) :: 'A','BC'])
  if (len(chars) /= 2) error stop 16
  if (size(chars) /= 2) error stop 17
  if (chars(1) /= 'A ') error stop 18
  if (chars(2) /= 'BC') error stop 19
end associate
end program p
