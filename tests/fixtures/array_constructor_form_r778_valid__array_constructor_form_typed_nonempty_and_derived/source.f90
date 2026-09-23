program p
implicit none
type rec
  integer :: marker
end type rec
type(rec) :: left, right
left%marker = 31
right%marker = 37
associate(ints => [integer :: 17,19,23])
  if (size(ints) /= 3) error stop 1
  if (ints(1) /= 17) error stop 2
  if (ints(2) /= 19) error stop 3
  if (ints(3) /= 23) error stop 4
end associate
associate(records => [rec :: left,right])
  if (size(records) /= 2) error stop 5
  if (records(1)%marker /= 31) error stop 6
  if (records(2)%marker /= 37) error stop 7
end associate
end program p
